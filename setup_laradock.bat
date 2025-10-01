@echo off
echo 🚀 DealNews Scraper - Laradock Integration Setup
echo ================================================

REM Check if .env exists
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy .env-template .env
    echo ✅ .env file created!
) else (
    echo ✅ .env file already exists
)

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo 🐍 Python found, setting up database...
    python setup_laradock_db.py
) else (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)

echo.
echo 🎉 Setup completed!
echo.
echo 📋 Next steps:
echo 1. Make sure your Laradock is running: docker ps
echo 2. Run the scraper: docker-compose up scraper
echo 3. Check your data at: http://localhost:8081 (phpMyAdmin)
echo.
echo ✅ Ready to scrape DealNews!
pause
