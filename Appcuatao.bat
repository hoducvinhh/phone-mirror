@echo off
title Appcuatao

set "PATH=C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools;%PATH%"

start "" pythonw "%~dp0appcuatao_bar.py"
scrcpy --window-title "Appcuatao" --no-window-aspect-ratio-lock --stay-awake --max-fps 60

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
