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

    def add_user(self, username):
        '''Adds a new user to the configuration with a unique UUID.'''
        user_id = self.generate_uuid()
        for inbound in self.data.get('inbounds', []):
            if not any(client['email'] == username for client in inbound['settings']['clients']):
                inbound['settings']['clients'].append({
                    'email': username,
                    'id': user_id,
                    'flow': 'xtls-rprx-vision',
                })
        self.save_data()
        return user_id

    def get_link(self, uuid, telegram_id, server_ip, public_key, inbound_index=0):
        '''Generates a VLESS link for the user.'''


        settings = self.data['inbounds'][inbound_index]
        port = settings['port']
        sni = settings['streamSettings']['realitySettings']['serverNames'][0]
        sid = settings['streamSettings']['realitySettings']['shortIds'][0]
        label = "Global High-Speed" if inbound_index == 0 else "Emergency Bypass"
        link = (
            f"vless://{uuid}@{server_ip}:{port}?"
            f"security=reality&sni={sni}&fp=chrome&pbk={public_key}"
            f"&type=tcp&sid={sid}&flow=xtls-rprx-vision#🇳🇱 NL | {label}"
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

            return round((data['interfaces'][0]['traffic']['day'][-1]['rx'] + data['interfaces'][-1]['traffic']['day'][0]['tx']) / (1024 * 1024 * 1024), 2)  # Convert to GB
        else:
            raise Exception("Failed to retrieve vnstat data: " + result.stderr)
    def vnstat_monthly_usage(self):
        '''Retrieves monthly network usage statistics using vnstat.'''
        result = subprocess.run(['vnstat', '-m', '--json'], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return round((data['interfaces'][0]['traffic']['month'][-1]['rx'] + data['interfaces'][0]['traffic']['month'][-1]['tx']) / (1024 * 1024 * 1024), 2)  # Convert to GB
        else:
            raise Exception("Failed to retrieve vnstat data: " + result.stderr)
    def get_xray_trafic(self, username):
        traffic_type = ['downlink', 'uplink']
        total_traffic = 0
        for t in traffic_type:
            cmd = ['xray', 'api','stats',f'--server={self.data["inbounds"][2]["listen"]}:{self.data["inbounds"][2]["port"]}',f'--name=user>>>{username}>>>traffic>>>{t}', '--reset']
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    total_traffic += data.get('stat', {}).get('value', 0)
                except Exception:
                    continue
            else:
                if 'not found' in result.stderr.lower():
                    logger.info(f"No traffic data found for user {username} and type {t}. Assuming 0.")
                    continue
                else:
                    raise Exception(f"Failed to retrieve xray traffic data for user {username} and type {t}: " + result.stderr)
        return total_traffic
        


