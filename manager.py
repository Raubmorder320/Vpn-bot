import json
import uuid
import subprocess
import re
import os
import logging

logger = logging.getLogger(__name__)


class Manager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.load_data()
        self.keys = self.generate_keys()

    def load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_data(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.data, file)

    def generate_uuid(self):
        '''Generates a unique UUID for a new user.'''
        return str(uuid.uuid4())

    def add_user(self, email):
        '''Adds a new user to the configuration with a unique UUID.'''
        user_id = self.generate_uuid()
        self.data['inbounds'][0]['settings']['clients'].append({
            'email': email,
            'id': user_id,
            'flow': 'xtls-rprx-vision',
        })
        self.save_data()
        return user_id

    def get_link(self, uuid, telegram_id, server_ip, public_key):
        '''Generates a VLESS link for the user.'''


        settings = self.data['inbounds'][0]['streamSettings']['realitySettings']
        sni = settings['serverNames'][0]
        sid = settings['shortIds'][0]
        link = (
            f"vless://{uuid}@{server_ip}:443?"
            f"security=reality&sni={sni}&fp=chrome&pbk={public_key}"
            f"&type=tcp&sid={sid}&flow=xtls-rprx-vision#Amsterdam_{telegram_id}"
        )
        return link
    def generate_keys(self):
        '''Generates public and private keys using xray.'''
        result = subprocess.run(['xray', 'x25519'], capture_output=True, text=True)
        if result.returncode == 0:
            keys = result.stdout.splitlines()
            private_key = re.search(r'PrivateKey:\s*(\S+)', keys[0]).group(1)
            public_key = re.search(r'\(PublicKey\):\s*(\S+)', keys[1]).group(1)
            return {'private': private_key, 'public': public_key}  # public_key, private_key
        else:
            raise Exception("Failed to generate keys: " + result.stderr)
    def restart_service(self):
        '''Restarts the xray service to apply changes.'''
        subprocess.run(['sudo', 'systemctl', 'restart', 'xray'], check=True)  

    def validate_config(self):
        '''Validates the current configuration using xray.'''
        result = subprocess.run(['xray', '-test', '-c', self.file_path], capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            return "Configuration is invalid: " + result.stderr
    def vnstat_daily_usage(self):
        '''Retrieves daily network usage statistics using vnstat.'''
        result = subprocess.run(['vnstat', '-d', '--json'], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return (data['interfaces'][0]['traffic']['day'][0]['rx'] + data['interfaces'][0]['traffic']['day'][0]['tx']) / (1024 * 1024 * 1024)  # Convert to GB
        else:
            raise Exception("Failed to retrieve vnstat data: " + result.stderr)
