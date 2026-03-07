@echo off
chcp 65001 >nul
echo ========================================
echo   SSH 密钥权限修复工具
echo ========================================
echo.

set SSH_KEY=%USERPROFILE%\.ssh\id_rsa

if not exist "%SSH_KEY%" (
    echo [错误] 未找到 SSH 密钥文件: %SSH_KEY%
    pause
    exit /b 1
)

echo 正在修复 SSH 密钥权限...
echo.

REM 禁用继承
icacls "%SSH_KEY%" /inheritance:r

REM 授予当前用户完全控制权限
icacls "%SSH_KEY%" /grant:r "%USERNAME%:F"

REM 移除其他用户权限
icacls "%SSH_KEY%" /remove "NT AUTHORITY\Authenticated Users"
icacls "%SSH_KEY%" /remove "BUILTIN\Users"
icacls "%SSH_KEY%" /remove "LAPTOP-9FCASCA9\CodexSandboxUsers"

echo.
echo ========================================
echo 权限修复完成
echo ========================================
echo.
echo 当前权限:
icacls "%SSH_KEY%"
echo.
pause
