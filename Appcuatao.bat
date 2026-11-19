@echo off
chcp 65001 >nul
title Appcuatao - Phản chiếu màn hình điện thoại

set ADB_PATH=C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools
set PATH=%ADB_PATH%;%PATH%

:: Tìm pythonw để khởi chạy thanh công cụ
set PYTHON_CMD=pythonw
if exist "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
)

:: Khởi chạy thanh công cụ Sidebar ở chế độ chạy ngầm
start "" %PYTHON_CMD% "%~dp0appcuatao_bar.py"

:: Khởi chạy cửa sổ phản chiếu màn hình
:: Bổ sung --no-window-aspect-ratio-lock để cho phép kéo dài ngang giữ nguyên cao, kéo dài cao giữ nguyên ngang
scrcpy --window-title "Appcuatao" --no-window-aspect-ratio-lock --stay-awake --max-fps 60

if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo [!] KHÔNG THỂ KẾT NỐI ĐIỆN THOẠI
    echo ======================================================================
    echo Vui lòng kiểm tra:
    echo   1. Cáp sạc USB đã cắm chắc chắn vào máy tính chưa?
    echo   2. Trên điện thoại đã bật 'Gỡ lỗi USB' (USB Debugging) chưa?
    echo   3. Đã bấm 'Cho phép' trên màn hình điện thoại chưa?
    echo ======================================================================
    echo.
    pause
)
