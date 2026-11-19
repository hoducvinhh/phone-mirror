@echo off
title Appcuatao

set "PATH=C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools;%PATH%"

set "PY_EXE=pythonw"
if exist "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
start "" "%PY_EXE%" "%~dp0appcuatao_bar.py"

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
