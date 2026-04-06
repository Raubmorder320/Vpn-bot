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

    def get_user_config(self, telegram_id, username,inbound_index=0):
        ''''Retrieves the VPN configuration link for the user with the given Telegram ID.'''
        user = self.db_manager.get_user(telegram_id)
        if not user:
            self.register_new_user(username, telegram_id)     
        return self.manager.get_link(user[3], telegram_id, self.server_ip, self.public_key, inbound_index)
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
            }
        else:
            return None
    def vnstat_daily_usage(self):
        '''Retrieves daily network usage statistics using vnstat.'''
        return self.manager.vnstat_daily_usage()