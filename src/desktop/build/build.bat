@echo off
REM 桌面端打包脚本（PyInstaller onedir，MVP 交付源码+脚本，不实际打包）
REM 用法：build\build.bat
setlocal
cd /d "%~dp0.."

if not exist ".venv" (
    echo [1/3] 创建虚拟环境...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [2/3] 安装依赖...
pip install -r requirements-desktop.txt pyinstaller

echo [3/3] 打包（onedir）...
pyinstaller --noconfirm build\pre-spc.spec

echo 完成：dist\pre-spc\pre-spc.exe
endlocal
