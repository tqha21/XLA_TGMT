@echo off
chcp 65001 >nul
title Khởi Chạy Celery Worker - ImageBench

echo =======================================================================
echo          CELERY ASYNCHRONOUS TASK WORKER (WINDOWS SOLO POOL)
echo =======================================================================
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo [*] Đang khởi động Celery Worker kết nối tới Redis Message Broker...
echo [*] LƯU Ý HỆ THỐNG:
echo     - Đảm bảo Redis Server đang chạy tại: redis://localhost:6379/0
echo     - Sử dụng '-P solo' để chạy an toàn trên hệ điều hành Windows.
echo.

celery -A make_celery:celery_app worker --loglevel=info -P solo

pause
