#!/usr/bin/env python3
"""
手机远程控制系统 - 交互式 CLI
整合所有功能的统一管理界面
"""
import json
import subprocess
import sys
import os
import webbrowser
from pathlib import Path

class PhoneCLI:
    def __init__(self):
        self.config_path = Path(__file__).parent / 'phone_config.json'
        self.config = self.load_config()
        self.wifi = None
        self.phone_ip = None
        self.nicknames = self.config.get('nicknames', {
            'user': '用户',
            'phone_agent': '手机OpenClaw',
            'desktop_agent': '桌面端AI'
        })
        self.user_name = self.nicknames.get('user', '用户')
        self.phone_agent_name = self.nicknames.get('phone_agent', '手机OpenClaw')
        self.update_network_info()

    def load_config(self):
        try:
            with open(self.config_path, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[错误] 无法加载配置文件: {e}")
            sys.exit(1)

    def update_network_info(self):
        """更新网络信息"""
        self.wifi = self.get_wifi()
        self.phone_ip = self.get_phone_ip()

    def get_wifi(self):
        """获取当前 WiFi 名称"""
        try:
            result = subprocess.run(
                'netsh wlan show interfaces',
                shell=True, capture_output=True, text=True, encoding='utf-8'
            )
            for line in result.stdout.split('\n'):
                if 'SSID' in line and ':' in line and 'BSSID' not in line:
                    return line.split(':')[1].strip()
        except:
            pass
        return '未知'

    def get_phone_ip(self):
        """获取手机 IP"""
        phone_ip = self.config['networks'].get(self.wifi, {}).get('phone_ip')
        if not phone_ip:
            phone_ip = self.config.get('default_network', {}).get('phone_ip',
                       self.config['networks'].get('default', {}).get('phone_ip', '未配置'))
        return phone_ip

    def ssh_cmd(self, cmd, timeout=10):
        """执行 SSH 命令"""
        ssh_user = self.config['ssh_config']['user']
        ssh_port = self.config['ssh_config']['port']
        full_cmd = f'ssh -p {ssh_port} -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} {ssh_user}@{self.phone_ip} "{cmd}"'
        return subprocess.run(full_cmd, shell=True, capture_output=True, text=True)

    def check_connection(self):
        """检查手机连接"""
        result = self.ssh_cmd('echo OK', timeout=3)
        return result.returncode == 0

    def check_tunnel(self):
        """检查隧道状态"""
        try:
            import urllib.request
            health_port = self.config['services']['openclaw']['health_port']
            urllib.request.urlopen(f'http://127.0.0.1:{health_port}/', timeout=2)
            return True
        except:
            return False

    def check_ports_occupied(self):
        """检查端口是否被占用"""
        ports = self.config['ssh_config']['ports_to_forward']
        occupied = []
        try:
            result = subprocess.run(
                'netstat -ano | findstr "LISTENING"',
                shell=True, capture_output=True, text=True
            )
            for port in ports:
                if f'127.0.0.1:{port}' in result.stdout or f'0.0.0.0:{port}' in result.stdout or f'[::]:{port}' in result.stdout:
                    occupied.append(port)
        except:
            pass
        return occupied

    def cleanup_tunnel(self):
        """清理已有隧道"""
        ports = self.config['ssh_config']['ports_to_forward']
        killed = []
        try:
            result = subprocess.run(
                'netstat -ano | findstr "LISTENING"',
                shell=True, capture_output=True, text=True
            )
            pids = set()
            for port in ports:
                for line in result.stdout.split('\n'):
                    line_lower = line.lower()
                    if f'127.0.0.1:{port}' in line_lower or f'0.0.0.0:{port}' in line_lower:
                        parts = line.split()
                        if len(parts) >= 5 and parts[-1].isdigit():
                            pid = parts[-1]
                            if pid != '0' and pid != '':
                                pids.add(pid)

            for pid in pids:
                try:
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True,
                                 capture_output=True, text=True)
                    killed.append(pid)
                except:
                    pass

            if not killed:
                try:
                    subprocess.run('taskkill /F /IM ssh.exe', shell=True,
                                 capture_output=True, text=True)
                    killed.append('ssh')
                except:
                    pass
        except:
            pass
        return killed

    def set_custom_ip(self, ip):
        """设置自定义手机 IP"""
        try:
            if self.wifi in self.config['networks']:
                self.config['networks'][self.wifi]['phone_ip'] = ip
            else:
                self.config['networks'][self.wifi] = {
                    'name': self.wifi,
                    'phone_ip': ip
                }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.phone_ip = ip
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def connect_tunnel(self):
        """建立 SSH 隧道"""
        ssh_user = self.config['ssh_config']['user']
        ssh_port = self.config['ssh_config']['port']
        ports = self.config['ssh_config']['ports_to_forward']
        port_args = ' '.join([f'-L {p}:127.0.0.1:{p}' for p in ports])
        cmd = f'ssh -N -f {port_args} -p {ssh_port} -o StrictHostKeyChecking=no -o ServerAliveInterval=60 {ssh_user}@{self.phone_ip}'
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                import time
                time.sleep(1)
                return True
            else:
                print(f"  错误: {result.stderr.strip()}")
                return False
        except subprocess.TimeoutExpired:
            return True
        except Exception as e:
            print(f"  错误: {e}")
            return False

    def open_termux(self):
        """打开 Termux SSH 连接"""
        ssh_user = self.config['ssh_config']['user']
        ssh_port = self.config['ssh_config']['port']
        cmd = f'ssh -p {ssh_port} -o StrictHostKeyChecking=no -o ServerAliveInterval=30 {ssh_user}@{self.phone_ip}'
        subprocess.run(cmd, shell=True)

    def send_msg(self, msg):
        """发送消息给手机 OpenClaw"""
        result = self.ssh_cmd(f'~/msgbus send kelao "{msg}"')
        return result.returncode == 0

    def recv_msg(self):
        """接收手机 OpenClaw 消息"""
        result = self.ssh_cmd('~/msgbus recv tuanzhang')
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def restore_adb(self):
        """恢复 ADB TCP 连接"""
        print("\n[步骤 1/2] 启用 ADB TCP（需要 USB 连接）")
        result = subprocess.run('/tmp/platform-tools/adb.exe tcpip 5555', shell=True)
        if result.returncode != 0:
            return False, "ADB TCP 启用失败，请确保手机已通过 USB 连接"

        print("[步骤 2/2] 连接到手机 ADB")
        result = self.ssh_cmd('adb connect localhost:5555')
        if result.returncode == 0:
            return True, "ADB 连接成功"
        return False, "ADB 连接失败"

    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """打印标题"""
        self.clear_screen()
        print("=" * 60)
        print("        手机远程控制系统 - 交互式管理界面")
        print("=" * 60)
        print(f"  用户: {self.user_name}")
        print(f"  手机Agent: {self.phone_agent_name}")
        print(f"  当前网络: {self.wifi}")
        print(f"  手机 IP: {self.phone_ip}")
        print("=" * 60)

    def print_menu(self):
        """打印主菜单"""
        print("\n主菜单:")
        print("  1. 系统状态检查")
        print("  2. 建立 SSH 隧道")
        print("  3. 打开 Web UI")
        print("  4. 打开 Code Server")
        print("  5. 连接 Termux 终端")
        print("  6. 桌面端Agent↔手机OpenClaw通讯指导")
        print("  7. 恢复 ADB 连接")
        print("  c. 清理 SSH 隧道")
        print("  i. 自定义配置")
        print("  0. 退出")
        print("-" * 60)

    def menu_status(self):
        """菜单：系统状态检查"""
        self.print_header()
        print("\n[功能] 系统状态检查")
        print("说明: 检查手机连接、SSH 隧道等状态\n")

        print("正在检查...")
        print(f"  网络环境: {self.wifi}")
        print(f"  手机 IP: {self.phone_ip}")

        print("  手机连接: ", end="", flush=True)
        if self.check_connection():
            print("✓ 正常")
        else:
            print("✗ 无法连接")

        print("  SSH 隧道: ", end="", flush=True)
        if self.check_tunnel():
            print("✓ 已建立")
        else:
            print("✗ 未建立")

    def menu_tunnel(self):
        """菜单：建立 SSH 隧道"""
        self.print_header()
        print("\n[功能] 建立 SSH 隧道")
        print("说明: 将手机端口转发到电脑，用于访问 Web UI 和 Code Server")
        print(f"转发端口: {', '.join(map(str, self.config['ssh_config']['ports_to_forward']))}\n")

        if self.check_tunnel():
            print("✓ 隧道已存在，无需重复建立")
            print(f"\n当前可访问服务:")
            print(f"  Web UI: http://127.0.0.1:{self.config['services']['openclaw']['webui_port']}")
            print(f"  Code Server: http://127.0.0.1:{self.config['services']['code_server']['port']}")
            return

        print("正在建立隧道，请稍候...")
        success = self.connect_tunnel()
        
        import time
        time.sleep(1)
        
        if self.check_tunnel():
            print("✓ 隧道建立成功!")
            print(f"\n可访问服务:")
            print(f"  Web UI: http://127.0.0.1:{self.config['services']['openclaw']['webui_port']}")
            print(f"  Code Server: http://127.0.0.1:{self.config['services']['code_server']['port']}")
        else:
            print("✗ 隧道建立失败")
            print("\n可能的解决方法:")
            print("  1. 检查手机是否在同一网络")
            print("  2. 检查手机 Termux 的 sshd 服务是否运行")
            print("  3. 确认手机 IP 配置正确")

    def fix_cors_config(self):
        """自动修复 CORS 配置，允许 127.0.0.1 访问"""
        try:
            import json
            
            result = self.ssh_cmd("cat ~/.openclaw/openclaw.json 2>/dev/null")
            if result.returncode != 0 or not result.stdout.strip():
                print("  ⚠ 无法读取配置文件，跳过自动修复")
                return False
            
            try:
                config = json.loads(result.stdout)
            except json.JSONDecodeError:
                print("  ⚠ 配置文件格式错误，跳过自动修复")
                return False
            
            needs_update = False
            origins_needed = ["http://localhost:18789", "http://127.0.0.1:18789"]
            
            if 'gateway' not in config:
                config['gateway'] = {}
            if 'controlUi' not in config['gateway']:
                config['gateway']['controlUi'] = {}
            if 'allowedOrigins' not in config['gateway']['controlUi']:
                config['gateway']['controlUi']['allowedOrigins'] = []
            
            origins = config['gateway']['controlUi']['allowedOrigins']
            for origin in origins_needed:
                if origin not in origins:
                    origins.append(origin)
                    needs_update = True
            
            if needs_update:
                print("  ✓ 发现需要更新 CORS 配置，正在修复...")
                new_config = json.dumps(config, indent=2, ensure_ascii=False)
                
                import base64
                config_b64 = base64.b64encode(new_config.encode('utf-8')).decode('ascii')
                
                cmd = f"echo '{config_b64}' | base64 -d > ~/.openclaw/openclaw.json"
                result = self.ssh_cmd(cmd)
                if result.returncode != 0:
                    print("  ⚠ 配置写入失败，尝试重启 Gateway")
                    result = self.ssh_cmd("openclaw gateway restart 2>/dev/null || pkill -f 'openclaw gateway'")
                    import time
                    time.sleep(2)
                    return False
                
                print("  ✓ CORS 配置已更新，正在重启 Gateway...")
                result = self.ssh_cmd("pkill -f 'openclaw gateway' 2>/dev/null; nohup openclaw gateway > /dev/null 2>&1 &")
                
                import time
                time.sleep(3)
                
                if self.check_tunnel():
                    print("  ✓ Gateway 已重启")
                    return True
                else:
                    print("  ⚠ Gateway 重启后健康检查未通过")
                    return False
            else:
                print("  ✓ CORS 配置已正确")
                
                result = self.ssh_cmd("pgrep -f 'openclaw gateway'")
                if result.returncode != 0 or not result.stdout.strip():
                    print("  ⚠ Gateway 未运行，正在启动...")
                    result = self.ssh_cmd("nohup openclaw gateway > /dev/null 2>&1 &")
                    import time
                    time.sleep(2)
                
                return True
                
        except Exception as e:
            print(f"  ⚠ 自动修复出错: {e}")
            return False

    def menu_webui(self):
        """菜单：打开 Web UI"""
        self.print_header()
        print("\n[功能] 打开 OpenClaw Web UI")
        print("说明: 在浏览器中管理手机端 Agent\n")

        if not self.check_tunnel():
            print("提示: 隧道未建立，正在自动建立...")
            if not self.connect_tunnel():
                print("✗ 隧道建立失败，无法打开 Web UI")
                return

        print("正在检查并修复 CORS 配置...")
        fix_result = self.fix_cors_config()
        
        url = f"http://127.0.0.1:{self.config['services']['openclaw']['webui_port']}"
        token = self.config['services']['openclaw']['token']
        
        print(f"\n正在打开: {url}")
        print(f"Gateway Token: {token}")
        
        import time
        time.sleep(0.5)
        webbrowser.open(url)
        
        print("\n✓ 已在浏览器中打开")
        
        if not fix_result:
            print("\n" + "=" * 50)
            print("【提示】如果出现 'origin not allowed' 错误：")
            print("\n已自动尝试修复，如仍有问题请手动执行：")
            ssh_cmd = f"ssh -p {self.config['ssh_config']['port']} {self.config['ssh_config']['user']}@{self.phone_ip}"
            print(f"  {ssh_cmd} \"openclaw gateway restart\"")
            print("=" * 50)

    def menu_code(self):
        """菜单：打开 Code Server"""
        self.print_header()
        print("\n[功能] 打开 Code Server")
        print("说明: 在浏览器中编辑手机端代码\n")

        if not self.check_tunnel():
            print("提示: 隧道未建立，正在自动建立...")
            if not self.connect_tunnel():
                print("✗ 隧道建立失败，无法打开 Code Server")
                return

        url = f"http://127.0.0.1:{self.config['services']['code_server']['port']}"
        password = self.config['services']['code_server']['password']
        print(f"正在打开: {url}")
        print(f"登录密码: {password}")
        webbrowser.open(url)
        print("✓ 已在浏览器中打开")

    def menu_termux(self):
        """菜单：连接 Termux"""
        self.print_header()
        print("\n[功能] 连接 Termux 终端")
        print("说明: 通过 SSH 连接到手机 Termux，可以直接输入命令")
        print("提示: 输入 'exit' 或按 Ctrl+D 退出\n")

        input("按回车键开始连接...")
        self.open_termux()

    def menu_agent_guide(self):
        """菜单：桌面端Agent与手机OpenClaw通讯指导"""
        self.print_header()
        print("\n[功能] 桌面端Agent ↔ 手机OpenClaw 通讯指导")
        print("=" * 60)
        print("\n【请将以下内容复制给桌面端AI（如Claude Code、OpenCode等）】\n")

        print("## 一、连接信息")
        print("-" * 40)
        print(f"手机 IP: {self.phone_ip}")
        print(f"SSH 端口: {self.config['ssh_config']['port']}")
        print(f"SSH 用户: {self.config['ssh_config']['user']}")
        print(f"配置文件: phone_config.json")

        print("\n## 二、通讯方式")
        print("-" * 40)
        print("\n【方式一：通过 SSH 执行命令】")
        print("  ssh -p <端口> <用户>@<手机IP> \"<命令>\"")
        print("  示例: ssh -p 8022 u0_a180@192.168.31.254 \"ls\"")

        print("\n【方式二：通过 OpenClaw API（需先建立SSH隧道）】")
        api_port = self.config['services']['openclaw']['api_port']
        token = self.config['services']['openclaw']['token']
        print(f"  API地址: http://127.0.0.1:{api_port}")
        print(f"  Token: <在phone_config.json中查看> (当前: {token[:8]}...)")

        print("\n【方式三：使用 msgbus 消息总线】")
        print("  (消息存储在手机的 ~/messages/ 目录)")
        print("  发送消息到手机:")
        print("    ssh -p <端口> <用户>@<手机IP> \"~/msgbus send <收件人> '消息内容'\"")
        print("    其中 <收件人> = tuanzhang (发送给手机OpenClaw)")
        print("  接收手机回复:")
        print("    ssh -p <端口> <用户>@<手机IP> \"~/msgbus recv tuanzhang\"")

        print("\n【方式四：使用 openclaw CLI】")
        print("  向手机上的 main agent 发送消息:")
        print("    ssh -p <端口> <用户>@<手机IP> \"openclaw agent --agent main -m '消息内容'\"")

        print("\n" + "=" * 60)
        print("\n提示: SSH隧道建立后，可直接访问:")
        print(f"  Web UI: http://127.0.0.1:{self.config['services']['openclaw']['webui_port']}")
        print(f"  Code Server: http://127.0.0.1:{self.config['services']['code_server']['port']}")

    def menu_adb(self):
        """菜单：恢复 ADB"""
        self.print_header()
        print("\n[功能] 恢复 ADB TCP 连接")
        print("说明: 手机重启后需要重新启用 ADB TCP")
        print("要求: 手机必须通过 USB 连接到电脑\n")

        input("请确保手机已通过 USB 连接，按回车继续...")
        success, msg = self.restore_adb()
        if success:
            print(f"✓ {msg}")
        else:
            print(f"✗ {msg}")

    def menu_cleanup(self):
        """菜单：清理隧道"""
        self.print_header()
        print("\n[功能] 清理 SSH 隧道")
        print("说明: 关闭所有已建立的 SSH 隧道进程\n")

        occupied = self.check_ports_occupied()
        if not occupied:
            print("没有发现占用的端口，隧道可能未建立")
            return

        print(f"发现占用端口: {occupied}")
        confirm = input("确认清理? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return

        print("正在清理...")
        killed = self.cleanup_tunnel()
        if killed:
            print(f"✓ 已清理进程: {killed}")
        else:
            print("✗ 清理失败或无进程需要清理")

    def menu_config(self):
        """菜单：自定义配置"""
        while True:
            self.print_header()
            print("\n[功能] 自定义配置")
            print("=" * 55)
            print("\n【必须配置】（根据手机OpenClaw实际值设置）:")
            print(f"  1. 用户昵称: {self.nicknames.get('user', '用户')}")
            print(f"  2. 手机Agent昵称: {self.nicknames.get('phone_agent', '手机OpenClaw')}")
            print(f"  3. 桌面端Agent昵称: {self.nicknames.get('desktop_agent', '桌面端AI')}")
            print(f"  4. 手机IP: {self.phone_ip} ({self.wifi})")
            
            token = self.config.get('services', {}).get('openclaw', {}).get('token', '')
            token_display = token[:12] + '...' if len(token) > 12 else token
            print(f"  5. Gateway Token: {token_display}")
            
            code_pwd = self.config.get('services', {}).get('code_server', {}).get('password', '')
            code_pwd_display = code_pwd[:8] + '...' if len(code_pwd) > 8 else code_pwd
            print(f"  6. Code Server密码: {code_pwd_display}")
            
            print("\n【可选配置】（建议维持默认，如需修改请进】:")
            print(f"  7. SSH/端口配置")
            print(f"  8. 高级服务配置")
            print(f"\n【工具】:")
            print(f"  9. 修复 WebUI 访问权限 (origin not allowed)")
            print(f"  a. 配置文件: {self.config_path}")
            print("\n" + "=" * 55)
            print("  0. 返回主菜单")
            print("-" * 55)

            choice = input("\n请选择 (0-9/a): ").strip().lower()

            if choice == '0':
                break
            elif choice == '1':
                self.config_nickname('user', '用户昵称')
            elif choice == '2':
                self.config_nickname('phone_agent', '手机Agent昵称')
            elif choice == '3':
                self.config_nickname('desktop_agent', '桌面端Agent昵称')
            elif choice == '4':
                self.config_phone_ip()
            elif choice == '5':
                self.config_gateway_token()
            elif choice == '6':
                self.config_code_server_password()
            elif choice == '7':
                self.menu_ssh_config()
            elif choice == '8':
                self.menu_services_config()
            elif choice == '9':
                self.fix_webui_access()
            elif choice == 'a':
                self.show_config_file()
            else:
                print("\n无效选择")

    def config_gateway_token(self):
        """配置Gateway Token"""
        self.print_header()
        print("\n[配置] Gateway Token")
        print("=" * 50)
        
        current = self.config.get('services', {}).get('openclaw', {}).get('token', '')
        print(f"当前值: {current[:16]}..." if len(current) > 16 else f"当前值: {current}")
        
        print("\n查询方法:")
        print("-" * 50)
        print("在手机 Termux 中执行:")
        print("  cat ~/.openclaw/openclaw.json | grep token")
        print("或")
        print("  openclaw config get gateway.auth.token")
        print("-" * 50)
        
        new_value = input("\n请输入新的Gateway Token (留空取消): ").strip()
        if not new_value:
            print("已取消")
            return
        
        if 'services' not in self.config:
            self.config['services'] = {}
        if 'openclaw' not in self.config['services']:
            self.config['services']['openclaw'] = {}
        
        self.config['services']['openclaw']['token'] = new_value
        
        if self.save_config():
            print(f"\n✓ Gateway Token 已更新")
        else:
            print("\n✗ 保存失败")

    def config_code_server_password(self):
        """配置Code Server密码"""
        self.print_header()
        print("\n[配置] Code Server 密码")
        print("=" * 50)
        
        current = self.config.get('services', {}).get('code_server', {}).get('password', '')
        print(f"当前值: {current[:8]}..." if len(current) > 8 else f"当前值: {current}")
        
        print("\n查询方法:")
        print("-" * 50)
        print("在手机 Termux 中执行:")
        print("  cat ~/.config/code-server/config.yaml")
        print("查找 password 字段")
        print("-" * 50)
        
        new_value = input("\n请输入新的Code Server密码 (留空取消): ").strip()
        if not new_value:
            print("已取消")
            return
        
        if 'services' not in self.config:
            self.config['services'] = {}
        if 'code_server' not in self.config['services']:
            self.config['services']['code_server'] = {}
        
        self.config['services']['code_server']['password'] = new_value
        
        if self.save_config():
            print(f"\n✓ Code Server密码 已更新")
        else:
            print("\n✗ 保存失败")

    def fix_webui_access(self):
        """修复 WebUI 访问权限 (origin not allowed)"""
        self.print_header()
        print("\n[工具] 修复 WebUI 访问权限")
        print("=" * 50)
        print("\n问题: 'origin not allowed' 错误")
        print("原因: OpenClaw Gateway 未允许 127.0.0.1 访问")
        print("\n正在自动修复...")
        
        if not self.check_connection():
            print("\n✗ 无法连接到手机，请检查网络和IP配置")
            return
        
        result = self.fix_cors_config()
        
        if result:
            print("\n✓ 修复成功！")
            print("\n请在浏览器中刷新 Web UI 页面:")
            port = self.config.get('services', {}).get('openclaw', {}).get('webui_port', 18789)
            print(f"  http://127.0.0.1:{port}")
        else:
            print("\n✗ 自动修复失败")
            print("\n请手动执行以下命令：")
            ssh_cmd = f"ssh -p {self.config['ssh_config']['port']} {self.config['ssh_config']['user']}@{self.phone_ip}"
            print(f"  {ssh_cmd}")
            print("  进入后执行: openclaw gateway restart")

    def menu_ssh_config(self):
        """SSH配置子菜单"""
        while True:
            self.print_header()
            print("\n[SSH/端口配置]")
            print("=" * 50)
            print("\n⚠  建议维持默认配置，除非清楚了解每个参数的作用")
            print("-" * 50)
            
            ssh_port = self.config.get('ssh_config', {}).get('port', 8022)
            ssh_user = self.config.get('ssh_config', {}).get('user', 'u0_aXXX')
            ports = self.config.get('ssh_config', {}).get('ports_to_forward', [])
            
            print(f"\n  1. SSH端口: {ssh_port} (默认8022)")
            print(f"  2. SSH用户名: {ssh_user} (在手机执行 'whoami' 查询)")
            print(f"  3. 转发端口: {ports}")
            
            print("\n" + "=" * 50)
            print("  0. 返回")
            print("-" * 50)
            
            choice = input("\n请选择 (0-3): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.config_ssh_param('port', 'SSH端口', '在手机执行: grep Port ~/.ssh/sshd_config')
            elif choice == '2':
                self.config_ssh_param('user', 'SSH用户名', '在手机执行: whoami')
            elif choice == '3':
                self.config_forward_ports()
            else:
                print("\n无效选择")

    def config_ssh_param(self, key, desc, hint):
        """配置SSH参数"""
        self.print_header()
        print(f"\n[配置] {desc}")
        print("=" * 50)
        
        current = self.config.get('ssh_config', {}).get(key, '')
        print(f"当前值: {current}")
        
        print(f"\n查询方法:")
        print("-" * 50)
        print(hint)
        print("-" * 50)
        
        new_value = input(f"\n请输入新的{desc} (留空取消): ").strip()
        if not new_value:
            print("已取消")
            return
        
        if 'ssh_config' not in self.config:
            self.config['ssh_config'] = {}
        
        if key == 'port':
            if not new_value.isdigit():
                print("\n✗ 请输入数字")
                return
            new_value = int(new_value)
        
        self.config['ssh_config'][key] = new_value
        
        if self.save_config():
            print(f"\n✓ {desc} 已更新为: {new_value}")
        else:
            print("\n✗ 保存失败")

    def config_forward_ports(self):
        """配置转发端口"""
        self.print_header()
        print("\n[配置] SSH转发端口")
        print("=" * 50)
        
        current = self.config.get('ssh_config', {}).get('ports_to_forward', [])
        print(f"当前值: {current}")
        
        print("\n说明:")
        print("-" * 50)
        print("标准端口说明:")
        print("  18789 - OpenClaw Web UI")
        print("  18791 - OpenClaw API")
        print("  18792 - OpenClaw 健康检查")
        print("  8080  - Code Server")
        print("-" * 50)
        print("⚠  修改可能导致功能失效，建议维持默认")
        
        new_value = input("\n请输入端口列表，用逗号分隔 (留空取消): ").strip()
        if not new_value:
            print("已取消")
            return
        
        try:
            ports = [int(p.strip()) for p in new_value.split(',')]
            if 'ssh_config' not in self.config:
                self.config['ssh_config'] = {}
            self.config['ssh_config']['ports_to_forward'] = ports
            
            if self.save_config():
                print(f"\n✓ 转发端口已更新为: {ports}")
            else:
                print("\n✗ 保存失败")
        except:
            print("\n✗ 格式错误，请输入数字用逗号分隔")

    def menu_services_config(self):
        """服务配置子菜单"""
        while True:
            self.print_header()
            print("\n[高级服务配置]")
            print("=" * 50)
            print("\n⚠  建议维持默认配置，除非清楚了解每个参数的作用")
            print("-" * 50)
            
            openclaw = self.config.get('services', {}).get('openclaw', {})
            code_server = self.config.get('services', {}).get('code_server', {})
            
            print(f"\n  1. OpenClaw Web UI端口: {openclaw.get('webui_port', 18789)}")
            print(f"  2. OpenClaw API端口: {openclaw.get('api_port', 18791)}")
            print(f"  3. OpenClaw健康检查端口: {openclaw.get('health_port', 18792)}")
            print(f"  4. Code Server端口: {code_server.get('port', 8080)}")
            
            print("\n" + "=" * 50)
            print("  0. 返回")
            print("-" * 50)
            
            choice = input("\n请选择 (0-4): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self.config_service_port('openclaw', 'webui_port', 'Web UI端口')
            elif choice == '2':
                self.config_service_port('openclaw', 'api_port', 'API端口')
            elif choice == '3':
                self.config_service_port('openclaw', 'health_port', '健康检查端口')
            elif choice == '4':
                self.config_service_port('code_server', 'port', 'Code Server端口')
            else:
                print("\n无效选择")

    def config_service_port(self, service, key, desc):
        """配置服务端口"""
        self.print_header()
        print(f"\n[配置] {desc}")
        print("=" * 50)
        
        current = self.config.get('services', {}).get(service, {}).get(key, '')
        print(f"当前值: {current}")
        
        print("\n⚠  修改端口可能导致服务无法访问")
        
        new_value = input(f"\n请输入新的{desc} (留空取消): ").strip()
        if not new_value:
            print("已取消")
            return
        
        if not new_value.isdigit():
            print("\n✗ 请输入数字")
            return
        
        new_value = int(new_value)
        
        if 'services' not in self.config:
            self.config['services'] = {}
        if service not in self.config['services']:
            self.config['services'][service] = {}
        
        self.config['services'][service][key] = new_value
        
        if self.save_config():
            print(f"\n✓ {desc} 已更新为: {new_value}")
        else:
            print("\n✗ 保存失败")

    def config_nickname(self, key, desc):
        """配置昵称"""
        self.print_header()
        print(f"\n[配置] {desc}")
        print("-" * 40)

        current = self.nicknames.get(key, '')
        print(f"当前值: {current if current else '(未设置)'}")

        new_value = input(f"\n请输入新的{desc} (留空取消): ").strip()
        if not new_value:
            print("已取消")
            return

        self.nicknames[key] = new_value
        self.config['nicknames'] = self.nicknames

        if self.save_config():
            print(f"\n✓ {desc}已更新为: {new_value}")

            if key == 'user':
                self.user_name = new_value
            elif key == 'phone_agent':
                self.phone_agent_name = new_value
        else:
            print("\n✗ 保存失败")

    def config_phone_ip(self):
        """配置手机IP"""
        self.print_header()
        print("\n[配置] 手机 IP 地址")
        print("=" * 50)
        print("\n说明: 为当前网络设置手机 IP 地址")
        print("\n查询手机IP的方法:")
        print("-" * 50)
        print("1. 在手机 Termux 中执行: ifconfig")
        print("   或: hostname -I")
        print("   查找 wlan0 或 eth0 的 IP 地址")
        print("\n2. 也可以在路由器管理界面查看")
        print("-" * 50)
        print(f"\n当前网络: {self.wifi}")
        print(f"当前 IP: {self.phone_ip}")

        new_ip = input("\n请输入新的手机 IP (留空取消): ").strip()
        if not new_ip:
            print("已取消")
            return

        parts = new_ip.split('.')
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            print("\n✗ IP 地址格式无效")
            return

        if self.set_custom_ip(new_ip):
            print(f"\n✓ IP 已更新为: {new_ip}")
        else:
            print("\n✗ IP 更新失败")

    def show_config_file(self):
        """显示配置文件位置和内容概要"""
        self.print_header()
        print("\n[配置文件信息]")
        print("=" * 50)
        print(f"\n配置文件位置:")
        print(f"  {self.config_path}")
        print("\n提示: 可直接编辑 JSON 文件进行高级配置")
        print("\n配置项说明:")
        print("  - nicknames: 角色昵称")
        print("  - networks: 各网络的手机IP")
        print("  - ssh_config: SSH连接配置")
        print("  - services: 服务端口和令牌")

    def menu_custom_ip(self):
        """菜单：自定义手机 IP（兼容旧入口）"""
        self.print_header()
        print("\n[功能] 自定义手机 IP")
        print("说明: 为当前网络设置自定义的手机 IP 地址\n")

        print("查询手机IP的方法:")
        print("-" * 50)
        print("在手机 Termux 中执行以下命令查询 IP:")
        print("  ifconfig")
        print("或")
        print("  hostname -I")
        print("-" * 50)
        print(f"\n当前网络: {self.wifi}")
        print(f"当前 IP: {self.phone_ip}")
        print()

        new_ip = input("请输入新的手机 IP (留空取消): ").strip()
        if not new_ip:
            print("已取消")
            return

        parts = new_ip.split('.')
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            print("✗ IP 地址格式无效")
            return

        print(f"正在设置 IP: {new_ip}")
        if self.set_custom_ip(new_ip):
            print(f"✓ IP 已更新为: {new_ip}")
            print(f"配置已保存到: {self.config_path}")
        else:
            print("✗ IP 更新失败")

    def run(self):
        """运行主循环"""
        while True:
            self.print_header()
            self.print_menu()

            choice = input("\n请选择功能 (0-7/c/i): ").strip().lower()

            if choice == '0':
                print("\n再见！")
                break
            elif choice == '1':
                self.menu_status()
            elif choice == '2':
                self.menu_tunnel()
            elif choice == '3':
                self.menu_webui()
            elif choice == '4':
                self.menu_code()
            elif choice == '5':
                self.menu_termux()
            elif choice == '6':
                self.menu_agent_guide()
            elif choice == '7':
                self.menu_adb()
            elif choice == 'c':
                self.menu_cleanup()
            elif choice == 'i':
                self.menu_config()
            else:
                print("\n无效选择，请重试")

            if choice != '0':
                input("\n按回车键返回主菜单...")

def main():
    try:
        cli = PhoneCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
