# OpenClaw Android Helper

A helper tool that enables users on Windows desktop to better manage OpenClaw Agent running on Android phones.

## System Architecture

```
┌─────────────────┐         SSH + ADB         ┌─────────────────┐
│   Desktop AI    │ ◄────────────────────────► │   Phone AI      │
│  (Claude Code)  │                            │(OpenClaw Agent) │
└─────────────────┘                            └─────────────────┘
       │                                               │
       │ Access via tunnel                             │ Control phone
       ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│  Browser Access │                            │  Android System │
│  - Web UI       │                            │  - Screenshot   │
│  - Code Server  │                            │  - Tap/Click    │
└─────────────────┘                            │  - UI Analysis  │
                                                └─────────────────┘
```

## Core Features

- 🔗 **SSH Tunnel** - Remotely access phone services
- 📱 **Phone Screen Control** - Screenshot, tap, swipe, text recognition
- 🌐 **Web UI** - Manage phone Agent via browser
- 💻 **Code Server** - Edit phone code in browser
- 🔄 **Message Bus** - Async communication between desktop and phone AI
- 🔧 **CDP Remote Debug** - Direct Chrome DOM manipulation for Web tasks

## Quick Start

### Prerequisites

- Windows/Mac/Linux PC
- Android phone with Termux installed
- Same WiFi network

### 1. Clone Project

```bash
git clone <your-repo-url>
cd openclaw-android-helper
```

### 2. Configure

Edit `phone_config.json`:

```json
{
  "nicknames": {
    "user": "Your Name",
    "phone_agent": "PhoneAgentName",
    "desktop_agent": "DesktopAgentName"
  },
  "networks": {
    "YourWiFi": {
      "name": "NetworkName",
      "phone_ip": "192.168.x.x"
    },
    "default": {
      "name": "DefaultNetwork",
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
      "token": "YourGatewayToken"
    },
    "code_server": {
      "port": 8080,
      "password": "YourCodeServerPassword"
    }
  },
  "adb": {
    "custom_path": "platform-tools\\adb.exe"
  }
}
```

### 3. Start CLI

```bash
# Windows
python phone_cli.py

# Or double-click start_cli.bat
```

### 4. Use Menu

```
Main Menu:
  0. Initialization Settings (First-time Use)
  1. System Status
  2. Establish SSH Tunnel
  3. Open Web UI
  4. Open Code Server
  5. Connect Termux Terminal
  6. Desktop ↔ Phone Communication Guide
  7. Restore ADB Connection
  c. Cleanup SSH Tunnel
  i. Configuration
  q. Exit
```

## Configuration Guide

### Configuration (i Menu)

| Item | Description | How to Get |
|------|-------------|------------|
| User Name | Your nickname | Enter directly |
| Phone Agent | Phone AI name | Enter directly |
| Desktop Agent | Desktop AI name | Enter directly |
| Phone IP | Phone's IP on current network | Run `ifconfig` or `hostname -I` on phone |
| Gateway Token | Web UI access token | Run `cat ~/.openclaw/openclaw.json \| grep token` on phone |
| Code Server Password | Code editor password | Run `cat ~/.config/code-server/config.yaml` on phone |

### SSH/Port Config (i → 7)

⚠️ Recommended to keep defaults

| Parameter | Default | Description |
|-----------|---------|-------------|
| SSH Port | 8022 | Termux SSH service port |
| SSH User | u0_aXXX | Run `whoami` on phone |
| Forward Ports | 18789,18791,18792,8080 | Ports forwarded via SSH tunnel |

## Core Files

| File | Description |
|------|-------------|
| `phone_cli.py` | Interactive CLI main program |
| `phone_manager.py` | Command-line management tool |
| `phone_config.json` | Configuration file |
| `phonectl.sh` | Phone control script |
| `phonectl_v2` | Enhanced phone control script |
| `msgbus` | Bidirectional message bus script |
| `cdp_agent.py` | Chrome DevTools Protocol agent |
| `browser_agent.py` | Browser automation example |

## Phone Setup

### 1. Install Termux

Install Termux from F-Droid: https://f-droid.org/packages/com.termux/

### 2. Initialize Environment

```bash
pkg update && pkg upgrade
pkg install -y git python nodejs openssh
```

### 3. Configure SSH

```bash
# Generate SSH key
ssh-keygen -t rsa -f ~/.ssh/id_rsa -N ""

# Start SSH service
sshd
```

### 4. Install OpenClaw

```bash
npm install -g openclaw
openclaw onboard
```

### 5. Deploy Control Scripts

Upload `phonectl.sh` and `msgbus` to phone:

```bash
scp -P 8022 phonectl.sh u0_aXXX@phoneIP:~/phonectl
scp -P 8022 msgbus u0_aXXX@~/msgbus
ssh -p 8022 u0_aXXX@phoneIP "chmod +x ~/phonectl ~/msgbus"
```

## Communication with Phone

### Method 1: SSH Command

```bash
ssh -p 8022 u0_aXXX@phoneIP "<command>"
```

### Method 2: msgbus Message Bus

```bash
# Send message to phone
ssh -p 8022 u0_aXXX@phoneIP "~/msgbus send tuanzhang 'message'"

# Receive phone reply
ssh -p 8022 u0_aXXX@phoneIP "~/msgbus recv tuanzhang"
```

### Method 3: OpenClaw CLI

```bash
ssh -p 8022 u0_aXXX@phoneIP "openclaw agent --agent main -m 'message'"
```

## Troubleshooting

### 1. SSH Connection Timeout

- Check if phone and PC are on same WiFi
- Verify phone IP is correct
- Check if Termux sshd service is running

### 2. Web UI Shows "origin not allowed"

Run CLI, select `i → 9` to fix, or manually run:

```bash
ssh -p 8022 u0_aXXX@phoneIP "openclaw gateway restart"
```

### 3. ADB Connection Lost

After phone restart, reconnect:

```bash
# PC side (requires USB connection)
adb tcpip 5555

# Phone Termux
adb connect localhost:5555
```

## Project Structure

```
openclaw-android-helper/
├── phone_cli.py          # Interactive CLI
├── phone_manager.py      # Command-line tool
├── phone_config.json     # Configuration file
├── phonectl.sh          # Phone control script
├── phonectl_v2          # Enhanced control script
├── msgbus               # Message bus script
├── cdp_agent.py         # CDP agent
├── browser_agent.py     # Browser automation
├── platform-tools/      # Android ADB tools
├── *.bat                # Windows shortcut scripts
├── SETUP_GUIDE.md       # Complete setup guide
├── phonectl_guide.md    # phonectl usage guide
└── ERROR_GUIDE.md      # Troubleshooting guide
```

## Support

- See `SETUP_GUIDE.md` for complete setup instructions
- See `ERROR_GUIDE.md` for troubleshooting
- See `phonectl_guide.md` for phone control commands

## License

MIT License
