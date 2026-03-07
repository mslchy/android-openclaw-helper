#!/usr/bin/env python3
import json
import subprocess
import sys
import os

config_path = os.path.join(os.path.dirname(__file__), 'phone_config.json')

def get_wifi():
    result = subprocess.run(
        'netsh wlan show interfaces',
        shell=True, capture_output=True, text=True, encoding='utf-8'
    )
    for line in result.stdout.split('\n'):
        if 'SSID' in line and ':' in line:
            return line.split(':')[1].strip()
    return ''

def get_phone_ip(config, wifi):
    phone_ip = config['networks'].get(wifi, {}).get('phone_ip')
    if not phone_ip:
        phone_ip = config['networks']['default']['phone_ip']
    return phone_ip

with open(config_path, encoding='utf-8') as f:
    config = json.load(f)

wifi = get_wifi()
phone_ip = get_phone_ip(config, wifi)

print(f"WiFi: {wifi}")
print(f"Phone IP: {phone_ip}")

# Step 1: Enable ADB TCP via USB
print("Step 1: Enabling ADB TCP on port 5555 (requires USB connection)...")
result = subprocess.run('/tmp/platform-tools/adb.exe tcpip 5555', shell=True)

if result.returncode != 0:
    print("[FAIL] Failed to enable ADB TCP. Make sure phone is connected via USB.")
    sys.exit(1)

print("[OK] ADB TCP enabled")

# Step 2: Connect via SSH and run adb connect
print(f"Step 2: Connecting to ADB via {phone_ip}...")
ssh_user = config['ssh_config']['user']
ssh_port = config['ssh_config']['port']

cmd = f'ssh -p {ssh_port} -o StrictHostKeyChecking=no {ssh_user}@{phone_ip} "adb connect localhost:5555"'
result = subprocess.run(cmd, shell=True)

if result.returncode == 0:
    print("[OK] ADB connection established")
else:
    print("[FAIL] ADB connection failed")
    sys.exit(1)
