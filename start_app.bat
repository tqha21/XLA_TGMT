@echo off
chcp 65001 >nul
title Khởi Chạy ImageBench - Hệ Thống Đánh Giá Định Dạng Ảnh

echo =======================================================================
echo          IMAGEBENCH - HỆ THỐNG ĐÁNH GIÁ & SO SÁNH ĐỊNH DẠNG ẢNH
echo =======================================================================
echo.

:: 1. Kiểm tra Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :PYTHON_FOUND
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set PY_CMD=py
    goto :PYTHON_FOUND
)

echo [!] LỖI: Chưa tìm thấy Python trên máy tính của bạn.
echo     Vui lòng tải và cài đặt Python từ: https://www.python.org/downloads/
echo     Lưu ý quan trọng: Nhớ tích chọn "Add python.exe to PATH" khi cài đặt!
echo.
pause
exit /b 1

:PYTHON_FOUND
echo [*] Đã nhận diện Python: 
%PY_CMD% --version
echo.

:: 2. Kiểm tra hoặc tạo môi trường ảo venv
if not exist "venv\Scripts\activate.bat" (
    echo [*] Đang khởi tạo môi trường ảo venv lần đầu tiên...
    %PY_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [!] Lỗi khi tạo môi trường ảo.
        pause
        exit /b 1
    )
    echo [v] Đã tạo môi trường ảo thành công.
    echo.
)

:: 3. Kích hoạt môi trường ảo
call venv\Scripts\activate.bat

:: 4. Kiểm tra và cài đặt thư viện
if not exist "venv\Lib\site-packages\flask" (
    echo [*] Đang cài đặt các thư viện cần thiết từ requirements.txt...
    echo     Quá trình này chỉ diễn ra trong lần đầu tiên, vui lòng đợi trong giây lát...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [!] Lỗi khi cài đặt thư viện. Vui lòng kiểm tra kết nối mạng.
        pause
        exit /b 1
    )
    echo [v] Đã cài đặt xong toàn bộ thư viện!
    echo.
)

:: 5. Mở trình duyệt sau 2 giây và chạy server
echo =======================================================================
echo [*] Đang khởi động Server tại địa chỉ: http://127.0.0.1:5000
echo [*] Trình duyệt web sẽ tự động mở sau vài giây...
echo [*] Bấm phím Ctrl + C để dừng máy chủ bất cứ lúc nào.
echo =======================================================================
echo.

start "" "http://127.0.0.1:5000"
python run.py

pause

