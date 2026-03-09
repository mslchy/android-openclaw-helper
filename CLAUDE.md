# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是 OpenClaw Android 小助手，让电脑端 AI (Claude Code) 能够通过 SSH + ADB 远程操控 Android 手机上的 OpenClaw Agent。

## 角色身份

在 `phone_config.json` 中配置：
- **用户**: 你的昵称
- **手机端 AI**: 手机OpenClaw
- **桌面端 AI**: Claude Code

## 连接架构

```
方式一：SSH + ADB + phonectl（截图/点击/UI分析）
电脑 (Claude Code)
  ↓ SSH -p <端口>
Termux (OpenClaw Agent)
  ↓ ADB localhost:5555
Android System
  ↓ input/screencap/uiautomator
屏幕操控 + 截图 + UI 分析

方式二：CDP 远程调试（直接操作 Chrome DOM，推荐用于 Web 任务）
电脑 Python (WebSocket localhost:9222)
  ↓ SSH 隧道 (9222 → 手机 9222)
Termux (ADB forward tcp:9222 → chrome_devtools_remote)
  ↓ Chrome DevTools Protocol
手机 Chrome 浏览器
  ↓ DOM 操作 / JS 执行 / 内容提取
```

## 常用命令

### 建立 SSH 隧道（访问 OpenClaw Web UI 和 API）

```bash
# 配置见 phone_config.json
ssh -N -f -L 18789:127.0.0.1:18789 -L 18791:127.0.0.1:18791 -L 18792:127.0.0.1:18792 -p <端口> -o StrictHostKeyChecking=no <用户>@<手机IP>
```

### 验证连接

```bash
curl http://127.0.0.1:18792/   # 应返回 OK
```

### 桌面端AI与手机OpenClaw双向通信（msgbus）

```bash
# 发消息给手机OpenClaw
ssh -p <端口> <用户>@<手机IP> "~/msgbus send tuanzhang '消息内容'"

# 读取手机OpenClaw的回复
ssh -p <端口> <用户>@<手机IP> "~/msgbus recv tuanzhang"

# 列出所有消息
ssh -p <端口> <用户>@<手机IP> "~/msgbus list tuanzhang"
```

手机OpenClaw端用法：
- 读取桌面端AI消息：`~/msgbus recv kelao`
- 回复桌面端AI：`~/msgbus send kelao "回复内容"`

消息存储在 `~/messages/` 目录，每条消息一个文件，读取后自动标记为已读。

### 向手机端 Agent 发送消息（openclaw CLI）

```bash
ssh -p <端口> -o StrictHostKeyChecking=no <用户>@<手机IP> "openclaw agent --agent main -m '消息内容'"
```

### 远程控制手机屏幕（通过 phonectl）

```bash
# 截图
ssh -p <端口> <用户>@<手机IP> "~/phonectl screenshot /sdcard/screen.png"

# 点击坐标
ssh -p <端口> <用户>@<手机IP> "~/phonectl tap 540 1170"

# 查找并点击文字
ssh -p <端口> <用户>@<手机IP> "~/phonectl tap_text '设置'"

# 打开网址
ssh -p <端口> <用户>@<手机IP> "~/phonectl open_url https://example.com"
```

### 手机重启后恢复 ADB（需要 USB 连接电脑）

```bash
# 电脑端
adb tcpip 5555
# 然后在 Termux 中：
adb connect localhost:5555
```

### CDP 远程调试手机 Chrome（Web 任务推荐）

```bash
# 1. 在手机上启动 Chrome（如果未运行）
ssh -p <端口> <用户>@<手机IP> "am start -n com.android.chrome/com.google.android.apps.chrome.Main"

# 2. ADB 转发 devtools socket 到 TCP 端口
ssh -p <端口> <用户>@<手机IP> "adb forward tcp:9222 localabstract:chrome_devtools_remote"

# 3. 建立 SSH 隧道
ssh -N -f -L 9222:127.0.0.1:9222 -p <端口> -o StrictHostKeyChecking=no <用户>@<手机IP>

# 4. 验证 CDP 连接
curl -s http://127.0.0.1:9222/json/version   # 应返回 Chrome 版本信息
curl -s http://127.0.0.1:9222/json            # 列出所有标签页
```

CDP 可以做的事：
- 直接用 CSS 选择器/XPath 定位元素（精确 100%）
- 执行 JavaScript 获取/修改页面内容
- 导航、点击、表单填写，无需截图+OCR
- 速度快几个数量级（毫秒级 vs 秒级）

Demo 脚本：`cdp_agent.py`（ChromeCDP 类封装了常用操作）

## phonectl 命令参考

脚本位于手机 Termux 的 `~/phonectl`，通过 ADB localhost:5555 控制手机。

| 命令 ||------|
| `tap <x> <y>` | 点击坐标 |
| `longpress 说明 |
|------ <x> <y> [ms]` | 长按，默认 1000ms |
| `swipe <x1> <y1> <x2> <y2> [ms]` | 滑动 |
| `scroll_up` / `scroll_down` | 上下翻页 |
| `home` / `back` / `power` / `enter` | 按键 |
| `screenshot [path]` | 截图，默认 `/sdcard/screen.png` |
| `current_app` | 查看当前应用包名 |
| `open_url <url>` | 用 Chrome 打开网址 |
| `launch_pkg <package>` | 按包名启动应用 |
| `uidump` | 输出完整 UI XML |
| `uidump_text` | 提取屏幕所有文字 |
| `uidump_json` | 结构化 JSON 输出所有 UI 元素（文字+类名+坐标） |
| `find_text <text>` | 查找文字坐标 |
| `tap_text <text>` | 直接点击文字 |
| `wait_stable [秒]` | 等待页面 UI 稳定，默认 10 秒 |
| `wait_text <文字> [秒]` | 等待指定文字出现，默认 15 秒 |
| `tap_and_wait <文字> [秒]` | 点击文字后等待页面稳定 |
| `input_text <文字>` | 输入文字（支持中文，需 ADBKeyboard） |
| `goto <快捷名>` | 快捷导航：zhihu_creator / zhihu_activity / settings / chrome |
| `shell <cmd>` | 执行任意 shell 命令 |

## 连接信息

从 `phone_config.json` 获取：
- **手机 IP**: 见配置文件 networks 部分
- **SSH 端口**: 见配置文件 ssh_config.port
- **SSH 用户**: 见配置文件 ssh_config.user
- **OpenClaw Gateway Token**: 见配置文件 services.openclaw.token
- **OpenClaw 端口**: 18789 (Web UI), 18791 (API), 18792 (健康检查)
- **手机屏幕分辨率**: 视设备而定
- **SSH 密钥**: 已配置免密登录 (`~/.ssh/id_rsa`)

## 注意事项

- ADB TCP 连接在手机重启后会断开，需要通过 USB 重新启用（`adb tcpip 5555`）
- 手机 IP 可能因 WiFi 重连而变化，连接失败时先检查 IP
- OpenClaw Agent 通信必须指定 `--agent main` 参数
- `phonectl` 使用 `input` 命令而非 `uinput`，适配华为等不支持 uinput 的设备
