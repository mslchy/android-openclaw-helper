@echo off
chcp 65001 >nul
echo 正在打开 OpenClaw Web UI...
python "%~dp0phone_manager.py" webui
