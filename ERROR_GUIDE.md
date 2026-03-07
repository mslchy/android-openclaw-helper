# 常见错误及解决方案

## SSH 相关错误

### 1. SSH 密钥权限错误

**错误信息**：
```
Bad permissions. Try removing permissions for user: ...
WARNING: UNPROTECTED PRIVATE KEY FILE!
Permissions for 'C:\\Users\\xxx/.ssh/id_rsa' are too open.
Permission denied (publickey).
```

**原因**：
- SSH 私钥文件权限过于开放
- Windows 上其他用户（如 CodexSandboxUsers）有权限访问私钥
- SSH 拒绝使用不安全的私钥文件

**解决方案**：
运行权限修复脚本：
```
双击 fix_ssh_permissions.bat
或
powershell -ExecutionPolicy Bypass -File fix_ssh_permissions.ps1
```

脚本会：
1. 禁用私钥文件的权限继承
2. 移除所有其他用户的访问权限
3. 只保留当前用户的完全控制权限

---

### 2. 端口绑定被拒绝

**错误信息**：
```
bind [127.0.0.1]:18789: Permission denied
channel_setup_fwd_listener_tcpip: cannot listen to port: 18789
Could not request local forwarding.
```

**原因**：
- 端口已被占用（通常是之前的 SSH 隧道还在运行）
- 多次建立隧道导致端口冲突

**解决方案**：
1. 清理已有隧道：
```
双击 cleanup_tunnel.bat
```

2. 或手动查找并结束进程：
```powershell
# 查看占用端口的进程
netstat -ano | findstr "18789"

# 结束进程（替换 PID）
taskkill /F /PID <进程ID>
```

**预防措施**：
- 使用 CLI 程序前先检查隧道状态
- 退出程序前清理隧道
- 避免重复建立隧道

---

### 3. SSH 连接超时

**错误信息**：
```
ssh: connect to host 192.168.x.x port 8022: Connection timed out
```

**原因**：
1. 手机 IP 地址变化（WiFi 重连后）
2. 手机不在同一网络
3. 手机 SSH 服务未运行
4. 防火墙阻止连接

**解决方案**：
1. 检查手机 IP：
   - 在手机 Termux 运行：`hostname -I`
   - 更新配置文件中的 IP

2. 检查手机 SSH 服务：
   - 在手机 Termux 运行：`pgrep sshd`
   - 如果没有输出，启动服务：`sshd`

3. 确认网络连接：
   - 手机和电脑在同一 WiFi
   - 尝试 ping 手机 IP：`ping 192.168.x.x`

---

### 4. SSH 连接被拒绝

**错误信息**：
```
ssh: connect to host 127.0.0.1 port 8022: Connection refused
```

**原因**：
- 尝试连接 127.0.0.1 但没有建立隧道
- 应该直接连接手机 IP

**解决方案**：
使用正确的连接方式：
```bash
# 直接连接手机（推荐）
ssh -p 8022 u0_aXXX@192.168.x.x

# 或使用 CLI 程序
python phone_cli.py
# 选择菜单 5（连接 Termux 终端）
```

---

## ADB 相关错误

### 5. ADB 连接失败

**错误信息**：
```
unable to connect to localhost:5555
```

**原因**：
- 手机重启后 ADB TCP 连接断开
- ADB 服务未启动

**解决方案**：
1. 通过 USB 连接手机到电脑
2. 运行 ADB 恢复脚本：
```
python restore_adb.py
```

脚本会：
1. 在电脑上启用 ADB TCP（端口 5555）
2. 通过 SSH 连接手机
3. 在手机上执行 `adb connect localhost:5555`

---

## 网络相关错误

### 6. 无法解析主机名

**错误信息**：
```
ssh: Could not resolve hostname phone: 不知道这样的主机
```

**原因**：
- SSH 配置文件未正确设置
- 配置文件路径错误

**解决方案**：
不使用主机名别名，直接使用 IP 地址：
```bash
ssh -p 8022 u0_aXXX@192.168.x.x
```

或使用 CLI 程序自动处理。

---

## 配置相关错误

### 7. 配置文件加载失败

**错误信息**：
```
[错误] 无法加载配置文件: ...
```

**原因**：
- phone_config.json 文件不存在或损坏
- JSON 格式错误

**解决方案**：
1. 检查配置文件是否存在
2. 验证 JSON 格式：
```bash
python -m json.tool phone_config.json
```

3. 如果损坏，参考 SETUP_GUIDE.md 重新创建

---

## 服务访问错误

### 8. Web UI 显示 "origin not allowed"

**错误信息**：
```
origin not allowed (open the Control UI from the gateway host or allow it in gateway.controlUi.allowedOrigins)
```

**原因**：
- OpenClaw Gateway 的 CORS 配置限制
- 访问来源不在允许列表中

**解决方案**：
已在配置中添加 `http://127.0.0.1:18789` 到 allowedOrigins。
如果仍有问题，重启 Gateway：
```bash
ssh -p 8022 u0_aXXX@手机IP "pkill -f 'openclaw gateway' && nohup openclaw gateway > /dev/null 2>&1 &"
```

---

### 9. Web UI 要求设备配对

**错误信息**：
```
pairing required
此设备需要网关主机的配对批准
```

**原因**：
- OpenClaw 的设备配对机制
- 浏览器设备 ID 变化

**解决方案**：
已在配置中禁用配对要求（`gateway.devices.pairing = 'off'`）。
如果仍需配对，在手机上批准：
```bash
ssh -p 8022 u0_aXXX@手机IP "openclaw devices list"
ssh -p 8022 u0_aXXX@手机IP "openclaw devices approve <requestId>"
```

---

## 故障排查流程

### 通用排查步骤

1. **检查网络连接**
   ```bash
   # 查看当前 WiFi
   netsh wlan show interfaces

   # Ping 手机
   ping 192.168.x.x
   ```

2. **检查手机 SSH 服务**
   ```bash
   ssh -p 8022 u0_aXXX@手机IP "pgrep sshd"
   ```

3. **检查隧道状态**
   ```bash
   netstat -ano | findstr "18789"
   ```

4. **查看手机端日志**
   ```bash
   ssh -p 8022 u0_aXXX@手机IP "tail -f ~/.openclaw/logs/*.log"
   ```

5. **清理并重新连接**
   ```bash
   # 清理隧道
   cleanup_tunnel.bat

   # 重新建立连接
   python phone_cli.py
   ```

---

## 预防措施

1. **定期检查系统状态**
   - 使用 CLI 程序的"系统状态检查"功能
   - 确保手机和电脑在同一网络

2. **避免重复操作**
   - 建立隧道前先检查是否已存在
   - 使用 CLI 程序统一管理

3. **保持配置更新**
   - 手机 IP 变化时及时更新配置
   - 使用 CLI 程序的自定义 IP 功能

4. **正确退出程序**
   - 退出前清理隧道
   - 避免留下僵尸进程

---

## 获取帮助

如果遇到未列出的错误：

1. 查看详细错误信息
2. 检查手机端日志
3. 参考 SETUP_GUIDE.md
4. 使用 CLI 程序的诊断功能
