from manager import Manager
from db_manager import DatabaseManager
import json
import os
import shutil
import logging
from dotenv import load_dotenv  

load_dotenv()

logger = logging.getLogger(__name__)


class VpnService:
    def __init__(self, config_path, template_path, data_dir, xray_api):
        '''Initializes the VPN service: prepares xray config, reality keys and the database.'''
        os.makedirs(data_dir, exist_ok=True)
        # При первом запуске создаём config.json из шаблона
        if not os.path.exists(config_path):
            shutil.copy(template_path, config_path)
        self.manager = Manager(config_path, xray_api)
        self.db_manager = DatabaseManager(os.path.join(data_dir, 'users.db'))
        self.server_ip = os.getenv("SERVER_IP")

        # Ключи reality генерируются один раз и хранятся в data/keys.json
        keys_path = os.path.join(data_dir, 'keys.json')
        if not os.path.exists(keys_path):
            keys = self.manager.generate_keys()
            with open(keys_path, 'w') as f:
                json.dump(keys, f)
        with open(keys_path) as f:
            keys = json.load(f)
        self.public_key = keys['public']
        self.private_key = keys['private']
        # Приватный ключ должен лежать в конфиге xray, публичный уходит клиентам в ссылке
        self.manager.set_private_key(self.private_key)



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

    def vnstat_daily_usage(self):
        '''Retrieves daily network usage statistics using vnstat.'''
        return self.manager.vnstat_daily_usage()
    def vnstat_monthly_usage(self):
        '''Retrieves monthly network usage statistics using vnstat.'''
        return self.manager.vnstat_monthly_usage()
    def get_all_users(self):
        '''Retrieves a list of all users from the database.'''
        return self.db_manager.get_all_users()
    def is_code_valid(self, code):
        '''Код существует и ещё не использован.'''
        row = self.db_manager.get_code(code)
        return row is not None and not row[3]  # row[3] = is_used
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
    def reset_all_traffic_usage(self):
        '''Resets the traffic usage for all users in the database.'''
        self.db_manager.reset_all_traffic_usage()

    def register_new_user(self, username, telegram_id):
        '''Registers a new user, adds them to the configuration, and restarts the service.'''
        if self.db_manager.get_user(telegram_id):
            raise Exception("User with this Telegram ID already exists.")
        uuid = self.manager.add_user(username)
        if not self.manager.validate_config():
            raise Exception("Invalid configuration after adding user.")
        # Применяем нового пользователя к работающему xray без перезапуска
        self.manager.apply_users()
        self.db_manager.add_user(username, telegram_id, uuid)
        return uuid
    def get_user_info(self, telegram_id):
        '''Retrieves user information from the database.'''
        user = self.db_manager.get_user_info(telegram_id)
        if user:
            user['server_ip'] = self.server_ip
            return user
        else:
            return None