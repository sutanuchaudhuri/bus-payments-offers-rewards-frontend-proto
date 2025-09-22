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
from agent_utils import MCPToolsManager, SessionManager, ContextManager, AgentOrchestrator, DatabaseManager

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

# Initialize database first using DatabaseManager
db_manager = DatabaseManager()
db_manager.init_database()

# Initialize components after database is ready
mcp_tools = MCPToolsManager(MCP_ENDPOINT_SSE)
orchestrator = AgentOrchestrator(mcp_tools, client)
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
        {'id': '1', 'name': 'Sutanu Chaudhuri'},

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

@app.route('/mcp-tools')
def mcp_tools_page():
    """MCP Tools listing page"""
    return render_template('mcp_tools.html')

@app.route('/api/mcp/tools')
def list_mcp_tools():
    """API endpoint to list all MCP tools with details"""
    try:
        tools_list = mcp_tools.get_tools_list()
        tools_count = mcp_tools.get_tools_count()

        return jsonify({
            'status': 'success',
            'total_tools': tools_count,
            'tools': tools_list,
            'endpoint': MCP_ENDPOINT_SSE
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'total_tools': 0,
            'tools': []
        }), 500

@app.route('/api/mcp/tool/<tool_id>/test', methods=['POST'])
def test_mcp_tool(tool_id):
    """Test a specific MCP tool"""
    try:
        data = request.get_json() or {}
        parameters = data.get('parameters', {})

        result = mcp_tools.call_tool(tool_id, parameters)

        return jsonify({
            'status': 'success',
            'tool_id': tool_id,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'tool_id': tool_id,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5010)
