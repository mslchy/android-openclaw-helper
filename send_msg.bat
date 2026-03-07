@echo off
chcp 65001 >nul
if "%~1"=="" (
    echo 用法: send_msg.bat "消息内容"
    pause
    exit /b 1
)
echo 正在发送消息给手机OpenClaw...
python "%~dp0phone_manager.py" send %*
pause
