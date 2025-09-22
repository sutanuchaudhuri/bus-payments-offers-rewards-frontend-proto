import sqlite3
import json
import uuid


class SessionManager:
    """Manage chat sessions with SQLite persistence"""

    @staticmethod
    def create_session(customer_id):
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        conn = sqlite3.connect('chat_sessions.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO sessions (id, customer_id, metadata)
            VALUES (?, ?, ?)
        ''', (session_id, customer_id, json.dumps({})))

        conn.commit()
        conn.close()

        return session_id

    @staticmethod
    def get_session(session_id):
        """Get session details"""
        conn = sqlite3.connect('chat_sessions.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        session = cursor.fetchone()

        conn.close()
        return session

    @staticmethod
    def add_message(session_id, message_type, content, agent_id=None, metadata=None, tool_calls=None):
        """Add message to chat history"""
        conn = sqlite3.connect('chat_sessions.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO chat_history (session_id, message_type, content, agent_id, metadata, tool_calls)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, message_type, content, agent_id,
              json.dumps(metadata or {}), json.dumps(tool_calls or [])))

        conn.commit()
        conn.close()

    @staticmethod
    def get_chat_history(session_id):
        """Get chat history for a session"""
        conn = sqlite3.connect('chat_sessions.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT message_type, content, agent_id, timestamp, metadata, tool_calls
            FROM chat_history
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))

        history = cursor.fetchall()
        conn.close()

        return [
            {
                'type': row[0],
                'content': row[1],
                'agent_id': row[2],
                'timestamp': row[3],
                'metadata': json.loads(row[4]) if row[4] else {},
                'tool_calls': json.loads(row[5]) if row[5] else []
            }
            for row in history
        ]
