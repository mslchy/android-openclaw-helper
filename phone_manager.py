#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import subprocess
import sys
import os
import webbrowser

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

config_path = os.path.join(os.path.dirname(__file__), 'phone_config.json')

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

def ssh_cmd(config, phone_ip, cmd):
    import os
    ssh_user = config['ssh_config']['user']
    ssh_port = config['ssh_config']['port']
    
    private_key = config['ssh_config'].get('private_key', '')
    if private_key:
        private_key = os.path.expandvars(private_key)
        if os.path.exists(private_key):
            key_arg = f'-i "{private_key}"'
        else:
            key_arg = ''
    else:
        key_arg = ''
    
    full_cmd = f'ssh {key_arg} -p {ssh_port} -o StrictHostKeyChecking=no {ssh_user}@{phone_ip} "{cmd}"'
    return subprocess.run(full_cmd, shell=True, capture_output=True, text=True)

def connect_tunnel(config, phone_ip):
    import os
    ssh_user = config['ssh_config']['user']
    ssh_port = config['ssh_config']['port']
    ports = config['ssh_config']['ports_to_forward']
    
    private_key = config['ssh_config'].get('private_key', '')
    if private_key:
        private_key = os.path.expandvars(private_key)
        if os.path.exists(private_key):
            key_arg = f'-i "{private_key}"'
        else:
            key_arg = ''
    else:
        key_arg = ''

    port_args = ' '.join([f'-L {p}:127.0.0.1:{p}' for p in ports])
    cmd = f'ssh {key_arg} -N -f {port_args} -p {ssh_port} -o StrictHostKeyChecking=no {ssh_user}@{phone_ip}'

    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def send_msg(config, phone_ip, msg):
    result = ssh_cmd(config, phone_ip, f'~/msgbus send tuanzhang "{msg}"')
    return result.returncode == 0

def recv_msg(config, phone_ip):
    result = ssh_cmd(config, phone_ip, '~/msgbus recv tuanzhang')
    return result.stdout.strip() if result.returncode == 0 else None

def main():
    if len(sys.argv) < 2:
        print("Usage: python phone_manager.py <command>")
        print("Commands:")
        print("  tunnel    - Establish SSH tunnel")
        print("  webui     - Open OpenClaw Web UI")
        print("  code      - Open code-server")
        print("  send <msg> - Send message to phoneOpenClaw (tuanzhang)")
        print("  recv      - Receive message from phoneOpenClaw")
        print("  all       - Connect tunnel and open services")
        sys.exit(1)

    config = load_config()
    wifi = get_wifi()
    phone_ip = get_phone_ip(config, wifi)

    print(f"WiFi: {wifi}")
    print(f"Phone IP: {phone_ip}")

    cmd = sys.argv[1]

    if cmd == 'tunnel':
        if connect_tunnel(config, phone_ip):
            print("[OK] Tunnel established")
        else:
            print("[FAIL] Tunnel failed")
            sys.exit(1)

    elif cmd == 'webui':
        webui_url = f"http://127.0.0.1:{config['services']['openclaw']['webui_port']}"
        print(f"Opening {webui_url}")
        webbrowser.open(webui_url)

    elif cmd == 'code':
        code_url = f"http://127.0.0.1:{config['services']['code_server']['port']}"
        print(f"Opening {code_url}")
        print(f"Password: {config['services']['code_server']['password']}")
        webbrowser.open(code_url)

    elif cmd == 'send':
        if len(sys.argv) < 3:
            print("Usage: python phone_manager.py send <message>")
            sys.exit(1)
        msg = ' '.join(sys.argv[2:])
        if send_msg(config, phone_ip, msg):
            print(f"[OK] Sent: {msg}")
        else:
            print("[FAIL] Send failed")

    elif cmd == 'recv':
        msg = recv_msg(config, phone_ip)
        if msg:
            print(f"Message: {msg}")
        else:
            print("No messages")

    elif cmd == 'all':
        print("Connecting tunnel...")
        if connect_tunnel(config, phone_ip):
            print("[OK] Tunnel established")
            print(f"Web UI: http://127.0.0.1:{config['services']['openclaw']['webui_port']}")
            print(f"Code Server: http://127.0.0.1:{config['services']['code_server']['port']}")
            print(f"Code Server Password: {config['services']['code_server']['password']}")
        else:
            print("[FAIL] Tunnel failed")
            sys.exit(1)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == '__main__':
    main()
