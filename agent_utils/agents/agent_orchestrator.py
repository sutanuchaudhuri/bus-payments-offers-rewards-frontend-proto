import sqlite3
import json
from datetime import datetime
from ..database import AgentsDAO


class AgentOrchestrator:
    """Orchestrate multiple agents for different tasks"""

    def __init__(self, mcp_tools, openai_client=None, db_path='chat_sessions.db'):
        self.mcp_tools = mcp_tools
        self.client = openai_client
        self.agents_dao = AgentsDAO(db_path)
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
        """Initialize agents in database using DAO"""
        for agent_id, agent_data in self.agents.items():
            self.agents_dao.create_or_update_agent(
                agent_id,
                agent_data['name'],
                agent_data['description'],
                agent_data['tools']
            )

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
            if self.client:  # Check if OpenAI client is available
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

                response = self.client.chat.completions.create(
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
