import os
import sqlite3
import json
import asyncio
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from openai import OpenAI
import uuid

# Import utility classes from agent_utils package
from agent_utils import MCPToolsManager, SessionManager, ContextManager

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configuration
MCP_ENDPOINT_SSE = os.getenv('MCP_ENDPOINT_SSE', 'http://127.0.0.1:8000/sse')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client with proper error handling
try:
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        client = None
        print("Warning: No OpenAI API key provided. AI responses will be simulated.")
except Exception as e:
    print(f"Warning: Could not initialize OpenAI client: {e}")
    client = None

# Database initialization
def init_db():
    """Initialize SQLite database for chat sessions and history"""
    conn = sqlite3.connect('chat_sessions.db')
    cursor = conn.cursor()

    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    ''')

    # Create chat history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT NOT NULL,
            agent_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            tool_calls TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')

    # Create agents table for multi-agent orchestration
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            tools TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create context table for session context management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_context (
            session_id TEXT PRIMARY KEY,
            context_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')

    conn.commit()
    conn.close()

# Agent Management with OpenAI Agents integration
class AgentOrchestrator:
    """Orchestrate multiple agents for different tasks"""

    def __init__(self, mcp_tools):
        self.mcp_tools = mcp_tools
        self.agents = {
            'payment_agent': {
                'name': 'Payment Processing Agent',
                'description': 'Handles payment-related queries and transactions',
                'tools': ['payment_processor', 'balance_checker', 'transaction_history'],
                'system_prompt': 'You are a payment processing agent for a bus transit system. Help customers with payments, balance inquiries, and transaction history.'
            },
            'offers_agent': {
                'name': 'Offers & Rewards Agent',
                'description': 'Manages offers, promotions, and rewards programs',
                'tools': ['offer_manager', 'rewards_calculator', 'promo_validator'],
                'system_prompt': 'You are an offers and rewards agent. Help customers find deals, apply promotions, and manage their rewards.'
            },
            'bus_schedule_agent': {
                'name': 'Bus Schedule Agent',
                'description': 'Provides bus schedules, routes, and timing information',
                'tools': ['schedule_lookup', 'route_planner', 'real_time_tracking'],
                'system_prompt': 'You are a bus schedule agent. Provide accurate schedule information, route planning, and real-time updates.'
            },
            'support_agent': {
                'name': 'Customer Support Agent',
                'description': 'General customer support and issue resolution',
                'tools': ['ticket_manager', 'faq_search', 'escalation_handler'],
                'system_prompt': 'You are a general customer support agent. Help with various inquiries and escalate complex issues when needed.'
            }
        }
        self._initialize_agents_db()

    def _initialize_agents_db(self):
        """Initialize agents in database"""
        conn = sqlite3.connect('chat_sessions.db')
        cursor = conn.cursor()

        for agent_id, agent_data in self.agents.items():
            cursor.execute('''
                INSERT OR REPLACE INTO agents (id, name, description, tools)
                VALUES (?, ?, ?, ?)
            ''', (agent_id, agent_data['name'], agent_data['description'],
                  json.dumps(agent_data['tools'])))

        conn.commit()
        conn.close()

    def get_appropriate_agent(self, message):
        """Determine which agent should handle the message using AI"""
        message_lower = message.lower()

        # Simple keyword-based routing (can be enhanced with ML)
        if any(word in message_lower for word in ['payment', 'pay', 'card', 'balance', 'transaction', 'refund']):
            return 'payment_agent'
        elif any(word in message_lower for word in ['offer', 'discount', 'reward', 'promotion', 'deal', 'points']):
            return 'offers_agent'
        elif any(word in message_lower for word in ['schedule', 'bus', 'route', 'time', 'arrival', 'departure']):
            return 'bus_schedule_agent'
        else:
            return 'support_agent'

    def process_with_agent(self, agent_id, message, context=None):
        """Process message with specific agent using OpenAI and MCP tools"""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"error": "Agent not found"}

        # Determine if tools are needed
        tools_to_call = self._determine_tools_needed(message, agent['tools'])
        tool_results = []

        # Call MCP tools if needed
        for tool_name in tools_to_call:
            if tool_name in self.mcp_tools.available_tools:
                # Extract parameters from message and context
                parameters = self._extract_tool_parameters(message, tool_name, context)
                result = self.mcp_tools.call_tool(tool_name, parameters)
                tool_results.append({
                    'tool': tool_name,
                    'result': result
                })

        # Generate AI response with tool results
        try:
            if client:  # Check if OpenAI client is available
                messages = [
                    {"role": "system", "content": agent['system_prompt']},
                    {"role": "user", "content": message}
                ]

                # Add tool results to context if available
                if tool_results:
                    tool_context = "Available tool results:\n"
                    for tool_result in tool_results:
                        tool_context += f"- {tool_result['tool']}: {tool_result['result']}\n"
                    messages.append({"role": "system", "content": tool_context})

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=500
                )

                ai_response = response.choices[0].message.content
            else:
                # Fallback response when OpenAI client is not available
                ai_response = f"I'm {agent['name']} and I'm here to help you with your {message}. I can assist with {', '.join(agent['tools'])} and other related tasks."

        except Exception as e:
            ai_response = f"I'm {agent['name']} and I'm here to help, but I'm experiencing technical difficulties. Please try again."

        return {
            "agent_id": agent_id,
            "agent_name": agent['name'],
            "response": ai_response,
            "tools_used": agent['tools'],
            "tool_calls": tool_results,
            "context": context or {}
        }

    def _determine_tools_needed(self, message, available_tools):
        """Determine which tools are needed for the message"""
        message_lower = message.lower()
        needed_tools = []

        tool_keywords = {
            'payment_processor': ['pay', 'payment', 'charge', 'transaction'],
            'balance_checker': ['balance', 'account', 'money', 'funds'],
            'schedule_lookup': ['schedule', 'time', 'when', 'arrival', 'departure'],
            'offer_manager': ['offer', 'deal', 'discount', 'promotion']
        }

        for tool in available_tools:
            if tool in tool_keywords:
                if any(keyword in message_lower for keyword in tool_keywords[tool]):
                    needed_tools.append(tool)

        return needed_tools

    def _extract_tool_parameters(self, message, tool_name, context):
        """Extract parameters for tool calls from message and context"""
        # Simple parameter extraction (can be enhanced with NLP)
        parameters = {}

        if context and 'customer_id' in context:
            parameters['customer_id'] = context['customer_id']

        # Add more sophisticated parameter extraction logic here
        return parameters

# Initialize database first
init_db()

# Initialize components after database is ready
mcp_tools = MCPToolsManager(MCP_ENDPOINT_SSE)
orchestrator = AgentOrchestrator(mcp_tools)
session_manager = SessionManager()
context_manager = ContextManager()

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/api/customers')
def get_customers():
    """Get list of customers for dropdown"""
    # Mock customer data - in real app, fetch from database
    customers = [
        {'id': 'CUST001', 'name': 'John Smith'},
        {'id': 'CUST002', 'name': 'Jane Doe'},
        {'id': 'CUST003', 'name': 'Bob Johnson'},
        {'id': 'CUST004', 'name': 'Alice Williams'},
        {'id': 'CUST005', 'name': 'Charlie Brown'}
    ]
    return jsonify(customers)

@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    """Start a new chat session"""
    data = request.get_json()
    customer_id = data.get('customer_id')

    if not customer_id:
        return jsonify({'error': 'Customer ID is required'}), 400

    # Create new session
    session_id = session_manager.create_session(customer_id)

    # Store in Flask session
    session['session_id'] = session_id
    session['customer_id'] = customer_id

    # Initialize context
    context_manager.update_context(session_id, 'customer_id', customer_id)
    context_manager.update_context(session_id, 'session_start', datetime.now().isoformat())

    return jsonify({
        'session_id': session_id,
        'customer_id': customer_id,
        'message': 'Chat session started successfully'
    })

@app.route('/api/chat/message', methods=['POST'])
def send_message():
    """Send a message and get agent response"""
    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    session_id = session.get('session_id')
    customer_id = session.get('customer_id')

    if not session_id:
        return jsonify({'error': 'No active session'}), 400

    # Save user message
    session_manager.add_message(session_id, 'user', message)

    # Determine appropriate agent
    agent_id = orchestrator.get_appropriate_agent(message)

    # Get current context
    context = context_manager.get_context(session_id)
    context['last_message'] = message
    context['message_count'] = context.get('message_count', 0) + 1

    # Process with agent
    agent_response = orchestrator.process_with_agent(agent_id, message, context)

    # Save agent response
    session_manager.add_message(
        session_id,
        'agent',
        agent_response['response'],
        agent_id,
        {'tools_used': agent_response['tools_used']},
        agent_response.get('tool_calls', [])
    )

    # Update context
    context_manager.update_context(session_id, 'last_agent', agent_id)
    context_manager.update_context(session_id, 'last_response', agent_response['response'])
    context_manager.update_context(session_id, 'message_count', context['message_count'])

    return jsonify({
        'response': agent_response['response'],
        'agent_id': agent_id,
        'agent_name': agent_response['agent_name'],
        'tools_used': agent_response['tools_used'],
        'tool_calls': agent_response.get('tool_calls', []),
        'session_id': session_id
    })

@app.route('/api/chat/history')
def get_chat_history():
    """Get chat history for current session"""
    session_id = session.get('session_id')

    if not session_id:
        return jsonify({'error': 'No active session'}), 400

    history = session_manager.get_chat_history(session_id)
    return jsonify(history)

@app.route('/api/agents')
def get_agents():
    """Get list of available agents"""
    return jsonify(orchestrator.agents)

@app.route('/api/tools')
def get_available_tools():
    """Get list of available MCP tools"""
    return jsonify(mcp_tools.available_tools)

@app.route('/api/visualization/session/<session_id>')
def get_session_visualization(session_id):
    """Get visualization data for a session"""
    history = session_manager.get_chat_history(session_id)
    context = context_manager.get_context(session_id)

    # Prepare visualization data
    agents_used = list(set([msg['agent_id'] for msg in history if msg['agent_id']]))
    tools_used = []
    for msg in history:
        if msg.get('tool_calls'):
            tools_used.extend([call['tool'] for call in msg['tool_calls']])

    viz_data = {
        'session_id': session_id,
        'message_count': len(history),
        'agents_used': agents_used,
        'tools_used': list(set(tools_used)),
        'context_keys': list(context.keys()),
        'timeline': [
            {
                'timestamp': msg['timestamp'],
                'type': msg['type'],
                'agent': msg['agent_id'],
                'tool_calls': len(msg.get('tool_calls', []))
            }
            for msg in history
        ]
    }

    return jsonify(viz_data)

@app.route('/api/context/<session_id>')
def get_session_context(session_id):
    """Get context for a session"""
    context = context_manager.get_context(session_id)
    return jsonify(context)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5010)
