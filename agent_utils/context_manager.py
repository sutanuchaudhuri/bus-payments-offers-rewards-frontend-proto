import json
from .database import ContextDAO


class ContextManager:
    """Manage conversation context and state with SQLite persistence"""

    def __init__(self, db_path='chat_sessions.db'):
        self.context_dao = ContextDAO(db_path)
        self.memory_store = {}  # In-memory cache

    def update_context(self, session_id, key, value):
        """Update context for a session"""
        # Update in-memory cache
        if session_id not in self.memory_store:
            self.memory_store[session_id] = {}
        self.memory_store[session_id][key] = value

        # Update database
        self.context_dao.save_context(session_id, self.memory_store[session_id])

    def get_context(self, session_id):
        """Get context for a session"""
        if session_id not in self.memory_store:
            self.memory_store[session_id] = self.context_dao.get_context(session_id)
        return self.memory_store.get(session_id, {})

    def clear_context(self, session_id):
        """Clear context for a session"""
        if session_id in self.memory_store:
            del self.memory_store[session_id]

        self.context_dao.delete_context(session_id)

    def get_context_keys(self, session_id):
        """Get all context keys for a session"""
        return self.context_dao.get_context_keys(session_id)

    def clear_context_field(self, session_id, key):
        """Remove a specific field from context"""
        if session_id in self.memory_store and key in self.memory_store[session_id]:
            del self.memory_store[session_id][key]

        self.context_dao.clear_context_field(session_id, key)
