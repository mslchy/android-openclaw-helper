# OpenClaw Android 小助手 - 完整指南

## 系统概述

这是一个 OpenClaw Android 小助手，让电脑端 AI（Claude Code）能够通过 SSH + ADB 远程操控 Android 手机上的 OpenClaw Agent。

### 架构设计

```
┌─────────────────┐         SSH + ADB         ┌─────────────────┐
│   电脑端 AI     │ ◄─────────────────────────► │   手机端 AI     │
│  (Claude Code)  │                            │ (OpenClaw Agent)│
│   - 桌面端AI    │                            │   - 手机OpenClaw │
└─────────────────┘                            └─────────────────┘
       │                                               │
       │ 通过隧道访问                                  │ 控制手机
       ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│  浏览器访问     │                            │  Android 系统   │
│  - Web UI       │                            │  - 截图/点击    │
│  - Code Server  │                            │  - UI 分析      │
└─────────────────┘                            └─────────────────┘
```

### 核心功能

- **远程控制**：通过 SSH 隧道远程控制手机屏幕
- **AI 协作**：电脑端与手机端 AI 双向通信
- **Web 管理界面**：OpenClaw Web UI 管理手机端 Agent
- **代码编辑**：通过 Code Server 在浏览器中编辑手机端代码
- **自动化操作**：支持 CDP（Chrome DevTools Protocol）直接操作 Web 应用

---

## 系统搭建教程

### 第一阶段：手机端准备

#### 1. 安装 Termux

```bash
# 在手机上安装 Termux（推荐 F-Droid 版本）
# 下载地址：https://f-droid.org/zh_Hans/packages/com.termux/
```

#### 2. 初始化 Termux 环境

```bash
# 更新软件包
pkg update && pkg upgrade

# 安装必要工具
pkg install -y git python nodejs openssh proot wget

# 设置 SSH 密钥（免密登录）
ssh-keygen -t rsa -f ~/.ssh/id_rsa -N ""
```

#### 3. 启用 ADB over TCP

```bash
# 安装 ADB
pkg install -y adb

# 首次需要 USB 连接电脑启用 TCP
# 在电脑上运行：
adb tcpip 5555

# 然后在手机 Termux 中：
adb connect localhost:5555

# 验证连接
adb devices
```

#### 4. 安装 OpenClaw

```bash
# 使用 npm 安装 OpenClaw
npm install -g openclaw

# 初始化配置
openclaw onboard

# 启动 Gateway
openclaw gateway
```

#### 5. 创建 phonectl 控制脚本

```bash
# 在手机 Termux 中创建 ~/phonectl
cat > ~/phonectl << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# phonectl - 手机控制脚本
ADB_PORT=5555
ADB_HOST=localhost

case "$1" in
    tap)
        adb -H $ADB_HOST -P $ADB_PORT shell input tap $2 $3
        ;;
    swipe)
        adb -H $ADB_HOST -P $ADB_PORT shell input swipe $2 $3 $4 $5 ${6:-500}
        ;;
    screenshot)
        adb -H $ADB_HOST -P $ADB_PORT exec-out screencap -p > "${2:-/sdcard/screen.png}"
        ;;
    uidump)
        adb -H $ADB_HOST -P $ADB_PORT shell uiautomator dump /sdcard/ui.xml
        adb -H $ADB_HOST -P $ADB_PORT shell cat /sdcard/ui.xml
        ;;
    *)
        echo "Usage: phonectl {tap|swipe|screenshot|uidump} ..."
        exit 1
esac
EOF

chmod +x ~/phonectl
```

#### 6. 创建 msgbus 消息总线

```bash
# 创建消息目录
mkdir -p ~/messages/kelao ~/messages/tuanzhang

# 创建 ~/msgbus 脚本
cat > ~/msgbus << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
MSG_DIR="$HOME/messages"

case "$1" in
    send)
        echo "$3" > "$MSG_DIR/$2/$(date +%s.%N).msg"
        echo "Message sent to $2"
        ;;
    recv)
        TARGET="$MSG_DIR/$2"
        UNREAD=$(ls -1t "$TARGET"/*.unread 2>/dev/null | head -1)
        if [ -n "$UNREAD" ]; then
            cat "$UNREAD"
            mv "$UNREAD" "${UNREAD%.unread}.read"
        else
            echo "No new messages"
        fi
        ;;
    list)
        ls -lt "$MSG_DIR/$2/" 2>/dev/null || echo "No messages"
        ;;
    *)
        echo "Usage: msgbus {send|recv|list} <target> [message]"
        exit 1
esac
EOF

chmod +x ~/msgbus
```

#### 7. 配置 OpenClaw Gateway

编辑 `~/.openclaw/openclaw.json`，添加以下配置：

```json
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "controlUi": {
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789"
      ]
    },
    "auth": {
      "mode": "token",
      "token": "你的随机token"
    },
    "devices": {
      "pairing": "off"
    }
  }
}
```

生成随机 token：

```bash
# 生成随机 token
openssl rand -hex 32
```

---

### 第二阶段：电脑端配置

#### 1. 准备工作

确保电脑已安装：
- Python 3.8+
- Git
- OpenSSH 客户端

#### 2. 克隆配置仓库

```bash
# 创建项目目录
mkdir -p ~/phone-control
cd ~/phone-control

# 初始化配置文件
```

#### 3. 创建 phone_config.json

```json
{
  "networks": {
    "家里WiFi名称": {
      "name": "家里",
      "phone_ip": "192.168.1.100"
    },
    "办公室WiFi名称": {
      "name": "办公室",
      "phone_ip": "192.168.2.100"
    }
  },
  "default_network": {
    "name": "默认",
    "phone_ip": "192.168.1.100"
  },
  "ssh_config": {
    "port": 8022,
    "user": "u0_a123",
    "ports_to_forward": [18789, 18791, 18792, 8080]
  },
  "services": {
    "openclaw": {
      "webui_port": 18789,
      "api_port": 18791,
      "health_port": 18792,
      "token": "你的token"
    },
    "code_server": {
      "port": 8080,
      "password": "你的密码"
    }
  }
}
```

**重要配置说明：**

1. **WiFi 名称匹配**：运行 `netsh wlan show interfaces` 查看当前 WiFi SSID
2. **手机 IP 获取**：在手机 Termux 中运行 `hostname -I` 查看
3. **SSH 端口**：默认 8022，Termux sshd 默认端口
4. **端口转发**：根据需要添加更多服务端口

#### 4. 创建管理脚本 phone_manager.py

```python
#!/usr/bin/env python3
"""
手机远程控制系统 - 管理脚本
"""
import json
import subprocess
import sys
import os
import webbrowser
from pathlib import Path

class PhoneManager:
    def __init__(self):
        self.config_path = Path(__file__).parent / 'phone_config.json'
        self.config = self.load_config()
        self.wifi = self.get_wifi()
        self.phone_ip = self.get_phone_ip()

    def load_config(self):
        with open(self.config_path, encoding='utf-8') as f:
            return json.load(f)

    def get_wifi(self):
        result = subprocess.run(
            'netsh wlan show interfaces',
            shell=True, capture_output=True, text=True, encoding='utf-8'
        )
        for line in result.stdout.split('\n'):
            if 'SSID' in line and ':' in line:
                return line.split(':')[1].strip()
        return ''

    def get_phone_ip(self):
        phone_ip = self.config['networks'].get(self.wifi, {}).get('phone_ip')
        if not phone_ip:
            phone_ip = self.config['default_network']['phone_ip']
        return phone_ip

    def ssh_cmd(self, cmd):
        ssh_user = self.config['ssh_config']['user']
        ssh_port = self.config['ssh_config']['port']
        full_cmd = f'ssh -p {ssh_port} -o StrictHostKeyChecking=no {ssh_user}@{self.phone_ip} "{cmd}"'
        return subprocess.run(full_cmd, shell=True, capture_output=True, text=True)

    def connect_tunnel(self):
        ssh_user = self.config['ssh_config']['user']
        ssh_port = self.config['ssh_config']['port']
        ports = self.config['ssh_config']['ports_to_forward']
        port_args = ' '.join([f'-L {p}:127.0.0.1:{p}' for p in ports])
        cmd = f'ssh -N -f {port_args} -p {ssh_port} -o StrictHostKeyChecking=no {ssh_user}@{self.phone_ip}'
        result = subprocess.run(cmd, shell=True)
        return result.returncode == 0

    def send_msg(self, msg):
        result = self.ssh_cmd(f'~/msgbus send kelao "{msg}"')
        return result.returncode == 0

    def recv_msg(self):
        result = self.ssh_cmd('~/msgbus recv tuanzhang')
        return result.stdout.strip() if result.returncode == 0 else None

    def check_tunnel(self):
        try:
            import urllib.request
            urllib.request.urlopen(f'http://127.0.0.1:{self.config["services"]["openclaw"]["health_port"]}/', timeout=2)
            return True
        except:
            return False

def main():
    if len(sys.argv) < 2:
        print("手机远程控制系统 - 管理脚本")
        print("\n用法: python phone_manager.py <命令>")
        print("\n可用命令:")
        print("  status   - 查看系统状态")
        print("  tunnel   - 建立 SSH 隧道")
        print("  webui    - 打开 OpenClaw Web UI")
        print("  code     - 打开 Code Server")
        print("  send <消息> - 发送消息给手机OpenClaw")
        print("  recv     - 接收手机OpenClaw消息")
        print("  all      - 连接所有服务")
        sys.exit(1)

    pm = PhoneManager()

    print(f"当前 WiFi: {pm.wifi}")
    print(f"手机 IP: {pm.phone_ip}")

    cmd = sys.argv[1]

    if cmd == 'status':
        print("\n系统状态检查:")
        tunnel_ok = pm.check_tunnel()
        print(f"  隧道状态: {'✓ 正常' if tunnel_ok else '✗ 未连接'}")

    elif cmd == 'tunnel':
        print("正在建立 SSH 隧道...")
        if pm.connect_tunnel():
            print("✓ 隧道建立成功")
            print(f"  Web UI: http://127.0.0.1:{pm.config['services']['openclaw']['webui_port']}")
            print(f"  Code Server: http://127.0.0.1:{pm.config['services']['code_server']['port']}")
        else:
            print("✗ 隧道建立失败")
            sys.exit(1)

    elif cmd == 'webui':
        url = f"http://127.0.0.1:{pm.config['services']['openclaw']['webui_port']}"
        print(f"打开 {url}")
        webbrowser.open(url)

    elif cmd == 'code':
        url = f"http://127.0.0.1:{pm.config['services']['code_server']['port']}"
        print(f"打开 {url}")
        print(f"密码: {pm.config['services']['code_server']['password']}")
        webbrowser.open(url)

    elif cmd == 'send':
        if len(sys.argv) < 3:
            print("用法: python phone_manager.py send <消息>")
            sys.exit(1)
        msg = ' '.join(sys.argv[2:])
        if pm.send_msg(msg):
            print(f"✓ 已发送: {msg}")
        else:
            print("✗ 发送失败")

    elif cmd == 'recv':
        msg = pm.recv_msg()
        if msg:
            print(f"收到消息: {msg}")
        else:
            print("没有新消息")

    elif cmd == 'all':
        print("正在连接所有服务...")
        if pm.connect_tunnel():
            print("✓ 隧道建立成功")
            print(f"\n访问地址:")
            print(f"  Web UI: http://127.0.0.1:{pm.config['services']['openclaw']['webui_port']}")
            print(f"  Code Server: http://127.0.0.1:{pm.config['services']['code_server']['port']}")
            print(f"\n认证信息:")
            print(f"  Gateway Token: {pm.config['services']['openclaw']['token']}")
            print(f"  Code Server 密码: {pm.config['services']['code_server']['password']}")
        else:
            print("✗ 隧道建立失败")
            sys.exit(1)

    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
```

#### 5. 创建快捷方式（Windows）

**start_all.bat**
```batch
@echo off
chcp 65001 >nul
echo ================================
echo 手机远程控制系统 - 一键启动
echo ================================
python "%~dp0phone_manager.py" all
pause
```

**check_status.bat**
```batch
@echo off
chcp 65001 >nul
python "%~dp0phone_manager.py" status
pause
```

---

### 第三阶段：网络配置

#### 1. 配置手机 SSH 服务

在手机 Termux 中：

```bash
# 安装 OpenSSH
pkg install openssh

# 启动 SSH 服务
sshd

# 查看手机 IP
hostname -I

# 查看 SSH 用户名（通常是 u0_aXXX）
whoami
```

#### 2. 测试 SSH 连接

在电脑上：

```bash
# 测试 SSH 连接
ssh -p 8022 u0_a123@手机IP

# 首次连接会提示确认，输入 yes
# 成功后会进入手机 Termux shell
```

#### 3. 配置免密登录（可选）

```bash
# 在电脑上生成 SSH 密钥（如果没有）
ssh-keygen -t rsa -b 4096

# 复制公钥到手机
ssh-copy-id -p 8022 u0_a123@手机IP

# 或手动复制
cat ~/.ssh/id_rsa.pub | ssh -p 8022 u0_a123@手机IP "cat >> ~/.ssh/authorized_keys"
```

---

## 操作指南

### 日常使用

#### 一键启动

双击 `start_all.bat`，系统会：
1. 自动检测当前 WiFi
2. 匹配对应的手机 IP
3. 建立 SSH 隧道
4. 显示所有服务访问地址

#### 访问服务

**OpenClaw Web UI**
- 地址：http://127.0.0.1:18789
- 用途：管理手机端 Agent、查看日志、配置技能

**Code Server**
- 地址：http://127.0.0.1:8080
- 密码：见配置文件
- 用途：在浏览器中编辑手机端代码

### 与手机OpenClaw通讯

**发送消息**
```bash
python phone_manager.py send "任务内容"
```

**接收消息**
```bash
python phone_manager.py recv
```

### 手机重启后恢复 ADB

当手机重启后，ADB TCP 连接会断开。恢复步骤：

1. 用 USB 线连接手机到电脑
2. 运行恢复脚本：
```bash
python restore_adb.py
```

脚本会：
1. 在电脑上启用 ADB TCP（端口 5555）
2. 通过 SSH 连接手机
3. 在手机上执行 `adb connect localhost:5555`

### 故障排查

#### 隧道连接失败

**症状**：运行脚本后提示连接超时

**排查步骤**：
1. 检查手机是否在同一网络
2. 检查手机 IP 是否变化（在 Termux 运行 `hostname -I`）
3. 检查 Termux SSH 是否运行（在手机运行 `pgrep sshd`）
4. 更新 `phone_config.json` 中的 IP 地址

#### Web UI 打开失败

**症状**：浏览器显示"origin not allowed"

**解决**：已在配置中添加 `http://127.0.0.1:18789` 到 allowedOrigins，重启 Gateway：
```bash
ssh -p 8022 u0_a123@手机IP "pkill -f 'openclaw gateway' && nohup openclaw gateway > /dev/null 2>&1 &"
```

#### Code Server 无法访问

**症状**：打开 http://127.0.0.1:8080 无响应

**排查步骤**：
1. 检查 code-server 是否运行：`ssh -p 8022 手机IP "pgrep code-server"`
2. 检查端口配置：`ssh -p 8022 手机IP "cat ~/.config/code-server/config.yaml"`
3. 重启 code-server：
```bash
ssh -p 8022 手机IP "pkill code-server && code-server"
```

---

## 高级功能

### CDP 远程调试（用于 Web 任务）

CDP（Chrome DevTools Protocol）可以直接操作 Chrome 的 DOM，无需截图+OCR，速度更快。

#### 启用 CDP

1. 在手机上启动 Chrome
2. ADB 转发 devtools socket：
```bash
ssh -p 8022 手机IP "adb forward tcp:9222 localabstract:chrome_devtools_remote"
```

3. 建立 SSH 隧道（已在配置中添加 9222 端口）

4. 验证连接：
```bash
curl -s http://127.0.0.1:9222/json/version
```

#### 使用 CDP Agent

项目提供了 `cdp_agent.py`，示例：

```python
from cdp_agent import ChromeCDP

# 连接到手机 Chrome
cdp = ChromeCDP("http://127.0.0.1:9222")

# 打开网页
cdp.navigate("https://example.com")

# 查找元素并点击
cdp.click("#submit-button")

# 输入文字
cdp.input("#username", "myname")

# 提取内容
text = cdp.get_text(".content")
```

---

## 安全建议

### 1. Token 管理

- 使用强随机 token（至少 32 字符）
- 定期更换 token
- 不要在公网暴露 Gateway

### 2. SSH 安全

- 使用密钥认证，禁用密码登录
- 限制 SSH 访问 IP（如可能）
- 定期检查 SSH 日志

### 3. 网络隔离

- 仅在可信网络使用（家庭/办公室）
- 避免在公共 WiFi 使用
- 考虑使用 VPN

---

## 附录：完整文件清单

### 电脑端必需文件

```
phone-control/
├── phone_config.json       # 网络和服务配置
├── phone_manager.py        # 主管理脚本
├── restore_adb.py          # ADB 恢复脚本
├── start_all.bat           # 一键启动（Windows）
├── check_status.bat        # 状态检查（Windows）
└── README.md               # 本文档
```

### 手机端必需文件

```
~/.openclaw/
├── openclaw.json          # OpenClaw 配置
└── ...

~/phonectl                 # 手机控制脚本
~/msgbus                   # 消息总线脚本
~/messages/                # 消息存储目录
├── kelao/
└── tuanzhang/
```

---

## 更新日志

- **2026-03-05**: 创建完整系统搭建教程和操作指南
- 支持多网络环境自动切换
- 一键启动所有服务
- 完善故障排查指南

---

## 技术支持

遇到问题？

1. 检查本文档的"故障排查"章节
2. 查看手机端日志：`ssh -p 8022 手机IP "tail -f ~/.openclaw/logs/*.log"`
3. 查看电脑端脚本输出信息

祝你使用愉快！
