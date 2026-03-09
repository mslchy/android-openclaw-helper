#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import subprocess
import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

config_path = Path(__file__).parent / 'phone_config.json'

def load_config():
    with open(config_path, encoding='utf-8') as f:
        return json.load(f)

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

def find_adb(config):
    """自动查找 ADB 路径"""
    adb_candidates = []
    
    custom_path = config.get('adb', {}).get('custom_path', '')
    if custom_path:
        adb_candidates.append(custom_path)
    
    if os.name == 'nt':
        adb_candidates.extend([
            'adb.exe',
            os.path.expanduser('~') + '\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe',
            os.path.expanduser('~') + '\\Android\\Sdk\\platform-tools\\adb.exe',
            'C:\\Android\\Sdk\\platform-tools\\adb.exe',
            'D:\\Android\\Sdk\\platform-tools\\adb.exe',
            os.environ.get('ANDROID_HOME', '') + '\\platform-tools\\adb.exe' if os.environ.get('ANDROID_HOME') else None,
        ])
        adb_candidates = [p for p in adb_candidates if p]
    else:
        adb_candidates.extend(['adb', '/usr/bin/adb'])
    
    for adb in adb_candidates:
        try:
            result = subprocess.run(f'"{adb}" version', shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"[OK] Found ADB: {adb}")
                return adb
        except:
            pass
    
    return None

def main():
    print("=" * 50)
    print("  ADB 连接恢复工具")
    print("=" * 50)
    
    config = load_config()
    wifi = get_wifi()
    phone_ip = get_phone_ip(config, wifi)

    print(f"\nWiFi: {wifi}")
    print(f"Phone IP: {phone_ip}")
    
    print("\n[Step 1/3] Finding ADB...")
    adb_path = find_adb(config)
    if not adb_path:
        print("[FAIL] ADB not found!")
        print("\nPlease:")
        print("  1. Install Android SDK")
        print("  2. Or set custom ADB path in phone_config.json")
        print("  3. Or use phone_cli.py menu: i -> 7 -> 4")
        sys.exit(1)
    
    print(f"\n[Step 2/3] Enabling ADB TCP (requires USB)...")
    result = subprocess.run(f'"{adb_path}" tcpip 5555', shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[FAIL] Failed to enable ADB TCP")
        print(f"Error: {result.stderr}")
        print("\nPlease ensure:")
        print("  1. Phone is connected via USB")
        print("  2. USB debugging is enabled on phone")
        print("  3. Computer is authorized on phone")
        sys.exit(1)
    
    print("[OK] ADB TCP enabled on port 5555")
    
    print("\n[Step 3/3] Connecting to phone ADB...")
    ssh_user = config['ssh_config']['user']
    ssh_port = config['ssh_config']['port']
    
    cmd = f'ssh -p {ssh_port} -o StrictHostKeyChecking=no {ssh_user}@{phone_ip} "adb connect localhost:5555"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("[OK] ADB connection established!")
        print("\nYou can now use:")
        print("  - phonectl for screen control")
        print("  - ADB commands like: adb shell")
    else:
        print(f"[FAIL] ADB connection failed")
        print(f"Error: {result.stderr}")
        sys.exit(1)

if __name__ == '__main__':
    main()
