@echo off
chcp 65001 >nul
echo 正在接收手机OpenClaw消息...
python "%~dp0phone_manager.py" recv
pause
