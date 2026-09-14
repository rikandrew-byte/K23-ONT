@echo off
chcp 65001 >nul
title Tạo Tập Luyện Viết Chữ Hán

:: Tìm Python thật (không phải Windows Store stub)
set PYTHON_PATH=C:\Users\rik_7\AppData\Local\Python\bin\python.exe

:: Kiểm tra tồn tại
if not exist "%PYTHON_PATH%" (
    echo Không tìm thấy Python tại: %PYTHON_PATH%
    echo Thử tìm trong PATH...
    
    :: Fallback: thử py launcher
    where py >nul 2>&1
    if %errorlevel%==0 (
        set PYTHON_PATH=py
    ) else (
        echo LỖI: Không tìm thấy Python!
        echo Vui lòng cài Python từ: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo Đang khởi động với: %PYTHON_PATH%
echo.

:: Kiểm tra thư viện
"%PYTHON_PATH%" -c "import reportlab, requests, PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo Đang cài thư viện cần thiết...
    "%PYTHON_PATH%" -m pip install reportlab requests pillow
    echo.
)

:: Chạy ứng dụng
"%PYTHON_PATH%" hanzi_workbook_gui.py

if %errorlevel% neq 0 (
    echo.
    echo Ứng dụng thoát với lỗi. Nhấn phím bất kỳ để xem log...
    "%PYTHON_PATH%" hanzi_workbook_gui.py 2>&1 | more
    pause
)
