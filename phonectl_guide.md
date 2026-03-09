# 手机OpenClaw控制工具 - phonectl 使用指南

## 快速开始

在 Termux 中直接使用 `~/phonectl` 命令控制手机。

## 核心功能

### 1. 查看屏幕
```bash
# 截图到 /sdcard/screen.png
~/phonectl screenshot

# 截图到指定位置
~/phonectl screenshot /sdcard/my_screen.png

# 查看当前应用
~/phonectl current_app
```

### 2. 操作屏幕
```bash
# 点击坐标 (x, y)
~/phonectl tap 540 1170

# 长按 1 秒
~/phonectl longpress 540 1170

# 长按 2 秒
~/phonectl longpress 540 1170 2000

# 滑动（从 x1,y1 到 x2,y2，持续 400ms）
~/phonectl swipe 540 1600 540 800 400

# 向上翻页
~/phonectl scroll_up

# 向下翻页
~/phonectl scroll_down
```

### 3. 按键操作
```bash
~/phonectl home      # 回主屏
~/phonectl back      # 返回
~/phonectl power     # 电源键
~/phonectl enter     # 回车
~/phonectl menu      # 菜单键
```

### 4. 打开应用和网址
```bash
# 打开网址（会用 Chrome 打开）
~/phonectl open_url https://www.google.com

# 按包名启动应用
~/phonectl launch_pkg com.android.chrome
```

### 5. UI 分析（查找元素）
```bash
# 提取屏幕上所有文字
~/phonectl uidump_text

# 查找文字的坐标
~/phonectl find_text "设置"

# 直接点击文字
~/phonectl tap_text "设置"

# 获取完整 UI 树
~/phonectl uidump
```

### 6. 执行任意命令
```bash
# 执行 shell 命令
~/phonectl shell "ls /sdcard/DCIM"
~/phonectl shell "cat /sdcard/test.txt"
```

## 实战示例

### 示例 1：打开百度并截图
```bash
~/phonectl open_url https://www.baidu.com
sleep 3
~/phonectl screenshot /sdcard/baidu.png
```

### 示例 2：查找并点击按钮
```bash
# 查找"搜索"按钮的位置
~/phonectl find_text "搜索"

# 直接点击"搜索"
~/phonectl tap_text "搜索"
```

### 示例 3：滚动页面并截图
```bash
~/phonectl scroll_down
sleep 1
~/phonectl screenshot /sdcard/page2.png
```

## 技术细节

- **屏幕分辨率**: 1080 x 2340
- **工作原理**: 通过 ADB localhost:5555 使用 `input` 命令控制
- **截图位置**: 默认 `/sdcard/screen.png`
- **当前应用**: Chrome 包名是 `com.android.chrome`

## 重启后恢复

手机重启后需要重新启用 ADB TCP：

```bash
# 在电脑上执行（需要 USB 连接）
/tmp/platform-tools/adb.exe tcpip 5555

# 然后在 Termux 中重新连接
adb connect localhost:5555
```

## 常见问题

**Q: 为什么 uidump_text 没有输出？**
A: 可能当前界面没有文字元素，或者 uiautomator 不支持该应用。

**Q: tap_text 找不到文字？**
A: 先用 `uidump_text` 查看屏幕上有哪些文字，确保关键词匹配。

**Q: 如何获取应用包名？**
A: 打开应用后执行 `~/phonectl current_app`

## 集成到手机OpenClaw工具链

手机OpenClaw可以通过 SSH 远程调用：

```bash
ssh -p 8022 u0_a180@192.168.137.174 "~/phonectl screenshot /sdcard/screen.png"
ssh -p 8022 u0_a180@192.168.137.174 "~/phonectl tap 540 1170"
ssh -p 8022 u0_a180@192.168.137.174 "~/phonectl open_url https://example.com"
```

或者在手机OpenClaw的代码中调用这些命令来控制手机。
