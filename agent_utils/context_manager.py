import sqlite3
import json


class ContextManager:
    """Manage conversation context and state with SQLite persistence"""

    def __init__(self):
        self.memory_store = {}  # In-memory cache

    def update_context(self, session_id, key, value):
        """Update context for a session"""
        # Update in-memory cache
        if session_id not in self.memory_store:
            self.memory_store[session_id] = {}
        self.memory_store[session_id][key] = value

        # Update database
        self._save_to_db(session_id)

    def get_context(self, session_id):
        """Get context for a session"""
        if session_id not in self.memory_store:
            self._load_from_db(session_id)
        return self.memory_store.get(session_id, {})

    def _save_to_db(self, session_id):
        """Save context to database"""
        conn = sqlite3.connect('chat_sessions.db')
        cursor = conn.cursor()

        context_data = json.dumps(self.memory_store.get(session_id, {}))
        cursor.execute('''
            INSERT OR REPLACE INTO session_context (session_id, context_data)
            VALUES (?, ?)
        ''', (session_id, context_data))

        conn.commit()
        conn.close()

    def _load_from_db(self, session_id):
        """Load context from database"""
        conn = sqlite3.connect('chat_sessions.db')
        cursor = conn.cursor()

        cursor.execute('SELECT context_data FROM session_context WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()

        if result:
            self.memory_store[session_id] = json.loads(result[0])
        else:
            self.memory_store[session_id] = {}

        conn.close()

    def clear_context(self, session_id):
        """Clear context for a session"""
        if session_id in self.memory_store:
            del self.memory_store[session_id]

        conn = sqlite3.connect('chat_sessions.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM session_context WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()

    def get_context_keys(self, session_id):
        """Get all context keys for a session"""
        context = self.get_context(session_id)
        return list(context.keys())

    def clear_context_field(self, session_id, key):
        """Remove a specific field from context"""
        if session_id in self.memory_store and key in self.memory_store[session_id]:
            del self.memory_store[session_id][key]
            self._save_to_db(session_id)
