import sqlite3
import os


class DatabaseManager:
    """Manage database connections and schema initialization"""

    def __init__(self, db_path='chat_sessions.db'):
        self.db_path = db_path

    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
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

    def drop_all_tables(self):
        """Drop all tables (useful for testing)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        tables = ['session_context', 'chat_history', 'agents', 'sessions']
        for table in tables:
            cursor.execute(f'DROP TABLE IF EXISTS {table}')

        conn.commit()
        conn.close()

    def get_table_info(self, table_name):
        """Get information about a table structure"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        info = cursor.fetchall()

        conn.close()
        return info

    def backup_database(self, backup_path):
        """Create a backup of the database"""
        import shutil
        shutil.copy2(self.db_path, backup_path)

    def restore_database(self, backup_path):
        """Restore database from backup"""
        import shutil
        shutil.copy2(backup_path, self.db_path)
