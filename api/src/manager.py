import json
import uuid
import subprocess
import re
import os
import logging
from xray_api import stats_pb2, stats_pb2_grpc
import grpc


logger = logging.getLogger(__name__)

class Manager:
    def __init__(self, file_path, xray_api):
        self.file_path = file_path
        self.xray_api = xray_api  # адрес API работающего xray, например "xray:10085"
        self.data = self.load_data()

    def load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_data(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.data, file, indent=4)

    def set_private_key(self, private_key):
        '''Записывает приватный ключ reality во все inbound'ы с security=reality.'''
        for inbound in self.data.get('inbounds', []):
            reality = inbound.get('streamSettings', {}).get('realitySettings')
            if reality is not None:
                reality['privateKey'] = private_key
        self.save_data()

    def apply_users(self):
        '''Добавляет пользователей из config.json в работающий xray без рестарта (xray api adu).
        Уже существующих пользователей xray пропускает.'''
        result = subprocess.run(
            ['xray', 'api', 'adu', f'--server={self.xray_api}', self.file_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            raise Exception("Failed to apply users to xray: " + result.stderr + result.stdout)
        logger.info(result.stdout.strip())

    def generate_uuid(self):
        '''Generates a unique UUID for a new user.'''
        return str(uuid.uuid4())

    def add_user(self, username):
        '''Adds a new user to the configuration with a unique UUID.'''
        user_id = self.generate_uuid()
        for inbound in self.data.get('inbounds', []):
            settings = inbound.get('settings', {})
            if 'clients' not in settings:
                # Если это технический порт (API), просто идем дальше
                continue
                
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


        inbounds = [i for i in self.data.get('inbounds', []) if 'clients' in i.get('settings', {})]
        if inbound_index >= len(inbounds):
            raise IndexError(f"Inbound {inbound_index} is not configured")
        settings = inbounds[inbound_index]
        port = settings['port']
        sni = settings['streamSettings']['realitySettings']['serverNames'][0]
        sid = settings['streamSettings']['realitySettings']['shortIds'][0]
        label = "Основной" if inbound_index == 0 else "Резервный"
        link = (
            f"vless://{uuid}@{server_ip}:{port}?"
            f"security=reality&sni={sni}&fp=chrome&pbk={public_key}"
            f"&type=tcp&sid={sid}&flow=xtls-rprx-vision#🐹 Hamsterdam | {label}"
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
    def validate_config(self):
        '''Validates the current configuration using xray.'''
        result = subprocess.run(['xray', '-test', '-c', self.file_path], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Configuration is invalid: " + result.stdout + result.stderr)
        return result.returncode == 0
    def vnstat_daily_usage(self):
        '''Retrieves daily network usage statistics using vnstat.'''
        result = subprocess.run(['vnstat', '-d', '--json'], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)

            today = data['interfaces'][0]['traffic']['day'][-1]
            return today['rx'] + today['tx']  # байты
        else:
            raise Exception("Failed to retrieve vnstat data: " + result.stderr)
    def vnstat_monthly_usage(self):
        '''Retrieves monthly network usage statistics using vnstat.'''
        result = subprocess.run(['vnstat', '-m', '--json'], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data['interfaces'][0]['traffic']['month'][-1]['rx'] + data['interfaces'][0]['traffic']['month'][-1]['tx'] 
        else:
            raise Exception("Failed to retrieve vnstat data: " + result.stderr)
    def get_xray_trafic(self, username):
        traffic_type = ['downlink', 'uplink']
        total_traffic = 0
        with grpc.insecure_channel(self.xray_api) as channel:
            stub = stats_pb2_grpc.StatsServiceStub(channel)
            for t in traffic_type:
                stat_name = f"user>>>{username}>>>traffic>>>{t}"
                request = stats_pb2.GetStatsRequest(name=stat_name, reset=True)
                try:
                    response = stub.GetStats(request)
                    total_traffic += response.stat.value
                except grpc.RpcError as e:
                    if e.code() == grpc.StatusCode.NOT_FOUND:
                        continue
                    else:
                        logger.error(f"gRPC error for {stat_name}: {e.code()} - {e.details()}")
        return total_traffic
        


