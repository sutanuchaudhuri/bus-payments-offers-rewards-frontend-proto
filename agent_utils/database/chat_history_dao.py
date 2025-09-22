import sqlite3
import json
from datetime import datetime


class ChatHistoryDAO:
    """Data Access Object for chat history operations"""

    def __init__(self, db_path='chat_sessions.db'):
        self.db_path = db_path

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def add_message(self, session_id, message_type, content, agent_id=None, metadata=None, tool_calls=None):
        """Add a message to chat history"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO chat_history (session_id, message_type, content, agent_id, metadata, tool_calls)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, message_type, content, agent_id,
              json.dumps(metadata or {}), json.dumps(tool_calls or [])))

        conn.commit()
        conn.close()

    def get_chat_history(self, session_id, limit=100):
        """Get chat history for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT message_type, content, agent_id, timestamp, metadata, tool_calls
            FROM chat_history
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (session_id, limit))

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

    def get_latest_messages(self, session_id, count=10):
        """Get the latest N messages from a session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT message_type, content, agent_id, timestamp, metadata, tool_calls
            FROM chat_history
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (session_id, count))

        history = cursor.fetchall()
        conn.close()

        # Reverse to get chronological order
        return [
            {
                'type': row[0],
                'content': row[1],
                'agent_id': row[2],
                'timestamp': row[3],
                'metadata': json.loads(row[4]) if row[4] else {},
                'tool_calls': json.loads(row[5]) if row[5] else []
            }
            for row in reversed(history)
        ]

    def get_message_count(self, session_id):
        """Get total message count for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM chat_history WHERE session_id = ?', (session_id,))
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def get_messages_by_agent(self, session_id, agent_id):
        """Get all messages from a specific agent in a session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT message_type, content, agent_id, timestamp, metadata, tool_calls
            FROM chat_history
            WHERE session_id = ? AND agent_id = ?
            ORDER BY timestamp ASC
        ''', (session_id, agent_id))

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

    def delete_message(self, message_id):
        """Delete a specific message"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM chat_history WHERE id = ?', (message_id,))

        conn.commit()
        conn.close()

    def clear_session_history(self, session_id):
        """Clear all chat history for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))

        conn.commit()
        conn.close()
