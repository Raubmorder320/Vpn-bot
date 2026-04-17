from manager import Manager
from db_manager import DatabaseManager
import json
import os
import logging
from dotenv import load_dotenv  

load_dotenv()

logger = logging.getLogger(__name__)

class VpnService:
    def __init__(self, config_path, db_path):
        '''Initializes the VPN service with the given configuration and database paths.'''
        self.manager = Manager(config_path)
        self.db_manager = DatabaseManager(db_path)
        self.server_ip = os.getenv("SERVER_IP")
        if not os.path.exists('keys.json'):
                
            keys = self.manager.generate_keys()
            self.public_key = keys['public']
            self.private_key = keys['private']
            json.dump(keys, open('keys.json', 'w'))
        else:
            keys = json.load(open('keys.json', 'r'))
            self.public_key = keys['public']
            self.private_key = keys['private']

    def register_new_user(self, username, telegram_id):
        '''Registers a new user, adds them to the configuration, and restarts the service.'''
        if self.db_manager.get_user(telegram_id):
            raise Exception("User with this Telegram ID already exists.")
        uuid = self.manager.add_user(username)
        self.db_manager.add_user(username, telegram_id, uuid)
        if not self.manager.validate_config():
            raise Exception("Invalid configuration after adding user.")
        self.restart_service()
        return uuid

    def get_user_config(self, telegram_id, username,inbound_index=0):
        ''''Retrieves the VPN configuration link for the user with the given Telegram ID.'''
        user = self.db_manager.get_user(telegram_id)
        if not user:
            uuid = self.register_new_user(username, telegram_id)
        else:
            uuid = user[3]
        return self.manager.get_link(uuid, telegram_id, self.server_ip, self.public_key, inbound_index)
    def validate_config(self):
        ''''Validates the current configuration using the manager.'''
        return self.manager.validate_config()

    def restart_service(self):
        '''Restarts the VPN service using the manager.'''
        self.manager.restart_service()
    def get_user_info(self, telegram_id):
        '''Retrieves user information from the database.'''
        user = self.db_manager.get_user_info(telegram_id)
        if user:
            return {
                'username': user['username'],
                'telegram_id': user['telegram_id'],
                'created_at': user['created_at'],
                'is_active': user['is_active']
            }
        else:
            return None
    def vnstat_daily_usage(self):
        '''Retrieves daily network usage statistics using vnstat.'''
        return self.manager.vnstat_daily_usage()
    def vnstat_monthly_usage(self):
        '''Retrieves monthly network usage statistics using vnstat.'''
        return self.manager.vnstat_monthly_usage()
    def get_all_users(self):
        '''Retrieves a list of all users from the database.'''
        return self.db_manager.get_all_users()
    def get_code(self, code):
        return self.db_manager.get_code(code)
    def mark_code_as_used(self, code):
        self.db_manager.mark_code_as_used(code)
    def generate_invite_code(self):
        '''Generates a new invite code using the database manager.'''
        return self.db_manager.generate_invite_code()
    def update_traffic_usage(self):
        '''Updates the traffic usage for a user in the database.'''
        users = self.db_manager.get_all_users()
        for user in users:
            usage = self.manager.get_xray_trafic(user[1])  # Assuming username is at index 1
            self.db_manager.add_traffic_usage(user[2], usage)  # Assuming telegram_id
