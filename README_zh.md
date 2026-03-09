# OpenClaw Android Helper

一个帮助用户在 Windows 桌面上更好地管理 Android 手机上运行的 OpenClaw Agent 的小助手。

## 系统架构

```
┌─────────────────┐         SSH + ADB         ┌─────────────────┐
│   桌面端 AI     │ ◄────────────────────────► │   手机端 AI     │
│  (Claude Code)  │                            │ (OpenClaw Agent)│
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

## 核心功能

- 🔗 **SSH 隧道连接** - 远程访问手机服务
- 📱 **手机屏幕控制** - 截图、点击、滑动、文字识别
- 🌐 **Web UI 管理** - 通过浏览器管理手机端 Agent
- 💻 **Code Server** - 在浏览器中编辑手机端代码
- 🔄 **双向消息总线** - 桌面端 AI 与手机端 AI 异步通信
- 🔧 **CDP 远程调试** - 直接操作 Chrome DOM，适用于 Web 任务

## 快速开始

### 前置要求

- Windows/Mac/Linux 电脑
- Android 手机（已安装 Termux）
- 同一 WiFi 网络

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd openclaw-android-helper
```

### 2. 配置文件

编辑 `phone_config.json`：

```json
{
  "nicknames": {
    "user": "你的昵称",
    "phone_agent": "手机Agent名称",
    "desktop_agent": "桌面端AI名称"
  },
  "networks": {
    "你的WiFi名称": {
      "name": "网络名称",
      "phone_ip": "192.168.x.x"
    },
    "default": {
      "name": "默认网络",
      "phone_ip": "192.168.x.x"
    }
  },
  "ssh_config": {
    "port": 8022,
    "user": "u0_aXXX",
    "ports_to_forward": [18789, 18791, 18792, 8080]
  },
  "services": {
    "openclaw": {
      "webui_port": 18789,
      "api_port": 18791,
      "health_port": 18792,
      "token": "你的GatewayToken"
    },
    "code_server": {
      "port": 8080,
      "password": "你的CodeServer密码"
    }
  },
  "adb": {
    "custom_path": "platform-tools\\adb.exe"
  }
}
```

### 3. 启动 CLI

```bash
# Windows
python phone_cli.py

# 或双击 start_cli.bat
```

### 4. 使用菜单

```
主菜单:
  0. 初始化设置（首次使用）
  1. 系统状态检查
  2. 建立 SSH 隧道
  3. 打开 Web UI
  4. 打开 Code Server
  5. 连接 Termux 终端
  6. 桌面端与手机OpenClaw通讯指导
  7. 恢复 ADB 连接
  c. 清理 SSH 隧道
  i. 自定义配置
  q. 退出
```

## 配置文件说明

### 自定义配置 (i 菜单)

| 配置项 | 说明 | 查询方法 |
|--------|------|----------|
| 用户昵称 | 你的称呼 | 直接输入 |
| 手机Agent昵称 | 手机端 AI 名称 | 直接输入 |
| 桌面端Agent昵称 | 桌面端 AI 名称 | 直接输入 |
| 手机IP | 手机在当前网络的 IP | 手机执行 `ifconfig` 或 `hostname -I` |
| Gateway Token | Web UI 访问令牌 | 手机执行 `cat ~/.openclaw/openclaw.json \| grep token` |
| Code Server密码 | 代码编辑器密码 | 手机执行 `cat ~/.config/code-server/config.yaml` |

### SSH/端口配置 (i → 7)

⚠️ 建议维持默认配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| SSH端口 | 8022 | Termux SSH 服务端口 |
| SSH用户名 | u0_aXXX | 在手机执行 `whoami` 查询 |
| 转发端口 | 18789,18791,18792,8080 | SSH 隧道转发的端口 |

## 核心文件

| 文件 | 说明 |
|------|------|
| `phone_cli.py` | 交互式 CLI 主程序 |
| `phone_manager.py` | 命令行管理工具 |
| `phone_config.json` | 配置文件 |
| `phonectl.sh` | 手机端控制脚本 |
| `phonectl_v2` | 增强版手机控制脚本 |
| `msgbus` | 双向消息总线脚本 |
| `cdp_agent.py` | Chrome DevTools Protocol 代理 |
| `browser_agent.py` | 浏览器自动化示例 |

## 手机端准备

### 1. 安装 Termux

从 F-Droid 安装 Termux：https://f-droid.org/packages/com.termux/

### 2. 初始化环境

```bash
pkg update && pkg upgrade
pkg install -y git python nodejs openssh
```

### 3. 配置 SSH

```bash
# 生成 SSH 密钥
ssh-keygen -t rsa -f ~/.ssh/id_rsa -N ""

# 启动 SSH 服务
sshd
```

### 4. 安装 OpenClaw

```bash
npm install -g openclaw
openclaw onboard
```

### 5. 部署控制脚本

将 `phonectl.sh` 和 `msgbus` 上传到手机：

```bash
scp -P 8022 phonectl.sh u0_aXXX@手机IP:~/phonectl
scp -P 8022 msgbus u0_aXXX@~/msgbus
ssh -p 8022 u0_aXXX@手机IP "chmod +x ~/phonectl ~/msgbus"
```

## 与手机通讯

### 方式一：SSH 执行命令

```bash
ssh -p 8022 u0_aXXX@手机IP "<命令>"
```

### 方式二：msgbus 消息总线

```bash
# 发送消息到手机
ssh -p 8022 u0_aXXX@手机IP "~/msgbus send tuanzhang '消息内容'"

# 接收手机回复
ssh -p 8022 u0_aXXX@手机IP "~/msgbus recv tuanzhang"
```

### 方式三：OpenClaw CLI

```bash
ssh -p 8022 u0_aXXX@手机IP "openclaw agent --agent main -m '消息内容'"
```

## 常见问题

### 1. SSH 连接超时

- 检查手机和电脑是否在同一 WiFi
- 确认手机 IP 是否正确
- 检查 Termux 的 sshd 服务是否运行

### 2. Web UI 显示 "origin not allowed"

运行 CLI，选择 `i → 9` 修复，或手动执行：

```bash
ssh -p 8022 u0_aXXX@手机IP "openclaw gateway restart"
```

### 3. ADB 连接断开

手机重启后需要重新连接：

```bash
# 电脑端（需要 USB 连接）
adb tcpip 5555

# 手机 Termux
adb connect localhost:5555
```

## 项目结构

```
openclaw-android-helper/
├── phone_cli.py          # 交互式 CLI
├── phone_manager.py      # 命令行工具
├── phone_config.json    # 配置文件
├── phonectl.sh          # 手机控制脚本
├── phonectl_v2         # 增强版控制脚本
├── msgbus              # 消息总线脚本
├── cdp_agent.py        # CDP 代理
├── browser_agent.py    # 浏览器自动化
├── platform-tools/     # Android ADB 工具
├── *.bat              # Windows 快捷脚本
├── SETUP_GUIDE.md     # 完整搭建教程
├── phonectl_guide.md  # phonectl 使用指南
└── ERROR_GUIDE.md    # 错误排查指南
```

## 技术支持

- 查看 `SETUP_GUIDE.md` 了解完整搭建流程
- 查看 `ERROR_GUIDE.md` 排查常见问题
- 查看 `phonectl_guide.md` 学习手机控制命令

## License

MIT License
