import json
import uuid
from .database import SessionDAO, ChatHistoryDAO


class SessionManager:
    """Manage chat sessions with SQLite persistence"""

    def __init__(self, db_path='chat_sessions.db'):
        self.session_dao = SessionDAO(db_path)
        self.chat_dao = ChatHistoryDAO(db_path)

    def create_session(self, customer_id):
        """Create a new chat session"""
        return self.session_dao.create_session(customer_id)

    def get_session(self, session_id):
        """Get session details"""
        return self.session_dao.get_session(session_id)

    def add_message(self, session_id, message_type, content, agent_id=None, metadata=None, tool_calls=None):
        """Add message to chat history"""
        self.chat_dao.add_message(session_id, message_type, content, agent_id, metadata, tool_calls)

    def get_chat_history(self, session_id):
        """Get chat history for a session"""
        return self.chat_dao.get_chat_history(session_id)

    def get_latest_messages(self, session_id, count=10):
        """Get the latest N messages from a session"""
        return self.chat_dao.get_latest_messages(session_id, count)

    def get_sessions_by_customer(self, customer_id, limit=10):
        """Get all sessions for a customer"""
        return self.session_dao.get_sessions_by_customer(customer_id, limit)

    def delete_session(self, session_id):
        """Delete a session and all related data"""
        self.session_dao.delete_session(session_id)
