@echo off
chcp 65001 >nul
echo 正在打开 Code Server...
python "%~dp0phone_manager.py" code
