@echo off
title Appcuatao_Launcher

set "PATH=C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools;C:\Users\Admin\scoop\shims;%PATH%"

set "PY_EXE=pythonw"
if exist "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
)

start "" "%PY_EXE%" "%~dp0appcuatao_bar.py"

scrcpy --window-title "Appcuatao" --video-codec=h265 --video-bit-rate=24M --max-size=1920 --video-buffer=0 --audio-buffer=20 --max-fps=60 --window-x 160 --window-y 60 --no-window-aspect-ratio-lock --stay-awake

:: Dong thanh tien ich ngay lap tuc khi scrcpy tat
taskkill /F /FI "WINDOWTITLE eq __Appcuatao_Docked_Ribbon__" >nul 2>&1

if %ERRORLEVEL% equ 0 goto :end

echo.
echo ========================================================
echo [!] KHONG THE KET NOI DIEN THOAI
echo ========================================================
echo Vui long kiem tra:
echo   1. Cap USB da cam chac chan vao may tinh.
echo   2. Tren dien thoai da bat USB Debugging.
echo   3. Man hinh dien thoai da sang va bam Cho phep.
echo ========================================================
echo.
pause

:end
