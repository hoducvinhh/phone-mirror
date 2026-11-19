@echo off
chcp 65001 >nul
title Appcuatao - Phản chiếu màn hình điện thoại

echo ======================================================================
echo                  APPCUATAO - PHẢN CHIẾU MÀN HÌNH ĐIỆN THOẠI
echo ======================================================================
echo.

set ADB_PATH=C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools
set PATH=%ADB_PATH%;%PATH%

:: Kiểm tra thiết bị kết nối
adb devices > "%TEMP%\adb_devices.txt"
findstr /R /C:"[0-9A-Za-z].*device$" "%TEMP%\adb_devices.txt" >nul
if errorlevel 1 (
    echo [!] CHƯA PHÁT HIỆN ĐIỆN THOẠI.
    echo.
    echo Bạn chỉ cần làm 2 bước sau:
    echo   1. Cắm cáp USB nối điện thoại vào máy tính.
    echo   2. Trên điện thoại: Bật "Gỡ lỗi USB" (USB Debugging) và chọn "Cho phép".
    echo.
    pause
    exit /b 1
)

echo [✓] Đã kết nối điện thoại thành công!
echo [*] Đang khởi chạy Appcuatao kèm thanh điều khiển bên cạnh...
echo.
echo ======================================================================
echo HƯỚNG DẪN KÍCH CỠ & THANH CÔNG CỤ:
echo   - Kéo ngang/dọc viền cửa sổ để thu phóng to nhỏ tùy ý.
echo   - Bấm nút [📐] trên thanh công cụ để TỰ ĐỘNG CĂN VỪA KHÍT (xóa viền đen).
echo   - Bấm nút [🔄] để XOAY NGANG MÀN HÌNH (xem phim 16:9).
echo   - Bấm nút [🔲] hoặc F11 để PHÓNG TO TOÀN MÀN HÌNH.
echo   - Bấm nút [⇄] ở đầu thanh để CHUYỂN THANH SANG BÊN TRÁI HOẶC BÊN PHẢI.
echo ======================================================================
echo.

:: Tìm pythonw để khởi chạy thanh điều khiển
set PYTHON_CMD=pythonw
if exist "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
)

:: Khởi chạy thanh công cụ Sidebar ở chế độ chạy ngầm
start "" %PYTHON_CMD% "%~dp0appcuatao_bar.py"

:: Khởi chạy cửa sổ phản chiếu màn hình
:: Bổ sung --no-window-aspect-ratio-lock để cho phép kéo dài ngang giữ nguyên cao, kéo dài cao giữ nguyên ngang
scrcpy --window-title "Appcuatao" --no-window-aspect-ratio-lock --stay-awake --max-fps 60

exit /b 0
