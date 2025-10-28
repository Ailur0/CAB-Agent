@echo off
echo ========================================
echo Change Management Teams Bot Launcher
echo ========================================
echo.

REM Check if ngrok is running
echo [1/3] Checking ngrok...
curl -s http://localhost:4040/api/tunnels > nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: ngrok doesn't seem to be running!
    echo Please run: ngrok http 3978
    echo.
    pause
    exit /b 1
)

echo OK - ngrok is running
echo.

REM Check environment variables
echo [2/3] Checking configuration...
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env file with your credentials.
    echo See TEAMS_SETUP.md for details.
    pause
    exit /b 1
)

echo OK - .env file found
echo.

REM Start the bot
echo [3/3] Starting Teams bot...
echo.
echo Bot will start on http://localhost:3978
echo Press Ctrl+C to stop
echo.

python src\bot\app.py

pause
