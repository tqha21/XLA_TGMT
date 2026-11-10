@echo off
chcp 65001 >nul
title Kiểm Thử Tự Động ImageBench (pytest)

echo =======================================================================
echo               CHẠY BỘ KIỂM THỬ TỰ ĐỘNG CHO IMAGEBENCH
echo =======================================================================
echo.

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo [*] Đang thực thi toàn bộ Test Suite với pytest...
echo.
pytest -v

echo.
echo =======================================================================
echo Hoàn thành kiểm thử!
echo =======================================================================
pause

