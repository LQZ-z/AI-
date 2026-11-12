@echo off
chcp 65001 >nul
cd /d %~dp0

python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --onedir --windowed --name ShiGuangAI --collect-all webview --hidden-import=webview.platforms.edgechromium desktop.py

if exist dist\ShiGuangAI (
    copy /Y users.json dist\ShiGuangAI\ >nul
    copy /Y history.json dist\ShiGuangAI\ >nul
    echo.
    echo 打包完成：dist\ShiGuangAI\ShiGuangAI.exe
) else (
    echo 打包失败，请检查上方错误信息
)

pause
