import sqlite3
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    telegram_id TEXT UNIQUE NOT NULL,
                    uuid TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                              )
            ''')

    def add_user(self, username, telegram_id, uuid):
        with self.conn:
            self.conn.execute('''
                INSERT INTO users (username, telegram_id, uuid) VALUES (?, ?, ?)
            ''', (username, telegram_id, uuid))

    def get_user_info(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'telegram_id': user[2],
                'uuid': user[3],
                'created_at': user[4],
                'is_active': user[5]
            }
        return None

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users')
        return cursor.fetchall()