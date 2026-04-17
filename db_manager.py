import sqlite3
import json
import logging
import uuid

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()
        self.create_invite_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    telegram_id TEXT UNIQUE NOT NULL,
                    uuid TEXT UNIQUE NOT NULL,
                    trafic_usage INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                              )
            ''')
    def create_invite_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS invites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_used BOOLEAN DEFAULT 0
                )
            ''')
    def generate_invite_code(self):
        code = "VPN_" + str(uuid.uuid4())
        with self.conn:
            self.conn.execute('''
                INSERT INTO invites (code) VALUES (?)
            ''', (code,))
        return code
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
                'is_active': user[5],
                'trafic_usage': user[6]
            }
        return None

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users')
        return cursor.fetchall()
    def get_user(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        return cursor.fetchone()
    def get_code(self, code):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM invites WHERE code = ?', (code,))
        return cursor.fetchone()
    def mark_code_as_used(self, code):
        with self.conn:
            self.conn.execute('''
                UPDATE invites SET is_used = 1 WHERE code = ?
            ''', (code,))
    def add_traffic_usage(self, telegram_id, usage):
        with self.conn:
            self.conn.execute('''
                UPDATE users SET trafic_usage = trafic_usage + ? WHERE telegram_id = ?
            ''', (usage, telegram_id))
        