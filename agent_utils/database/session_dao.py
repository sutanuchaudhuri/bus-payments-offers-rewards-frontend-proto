import sqlite3
import json
import uuid
from datetime import datetime


class SessionDAO:
    """Data Access Object for session operations"""

    def __init__(self, db_path='chat_sessions.db'):
        self.db_path = db_path

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def create_session(self, customer_id, metadata=None):
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO sessions (id, customer_id, metadata)
            VALUES (?, ?, ?)
        ''', (session_id, customer_id, json.dumps(metadata or {})))

        conn.commit()
        conn.close()

        return session_id

    def get_session(self, session_id):
        """Get session details by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        session = cursor.fetchone()

        conn.close()
        return session

    def get_sessions_by_customer(self, customer_id, limit=10):
        """Get all sessions for a customer"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM sessions 
            WHERE customer_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (customer_id, limit))

        sessions = cursor.fetchall()
        conn.close()
        return sessions

    def update_session_metadata(self, session_id, metadata):
        """Update session metadata"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE sessions 
            SET metadata = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (json.dumps(metadata), session_id))

        conn.commit()
        conn.close()

    def delete_session(self, session_id):
        """Delete a session and all related data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Delete in order due to foreign key constraints
        cursor.execute('DELETE FROM session_context WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))

        conn.commit()
        conn.close()

    def get_all_sessions(self, limit=50):
        """Get all sessions (for admin purposes)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, customer_id, created_at, updated_at 
            FROM sessions 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))

        sessions = cursor.fetchall()
        conn.close()
        return sessions
