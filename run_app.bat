@echo off
title Khedut & Vepari Hisab ERP
echo ========================================================
echo   Khedut & Vepari Hisab ERP (Django & Database)
echo ========================================================
echo.
echo Checking Python and Django installation...
python -c "import django" >nul 2>&1
if errorlevel 1 (
    echo Django is not installed. Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies. Please ensure Python and pip are in your PATH.
        pause
        exit /b 1
    )
)

echo Starting Django development server...
echo URL: http://127.0.0.1:8000/
echo Admin: http://127.0.0.1:8000/admin/ (User: admin / Pass: admin)
echo ========================================================
echo.
start http://127.0.0.1:8000/
python manage.py runserver 127.0.0.1:8000
pause
