@echo off
chcp 65001 >nul
echo 正在建立 SSH 隧道...
python "%~dp0phone_manager.py" tunnel
pause
