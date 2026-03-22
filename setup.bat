@echo off
REM ============================================================
REM Secure File Locker — Windows Local Setup
REM 21IPE315P — Cloud Product and Platform Engineering
REM
REM Run this ONCE to set up the project:
REM   Double-click setup.bat
REM ============================================================

echo ================================================
echo  Secure File Locker — Local Setup
echo  21IPE315P Cloud Product and Platform Engineering
echo ================================================
echo.

REM Check Docker is running
docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not running!
    echo Please install Docker Desktop from docker.com
    echo Then restart and run this script again.
    pause
    exit /b 1
)

echo Docker found! Continuing...
echo.

REM Generate secret keys
echo Generating secret keys...
for /f %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set SECRET_KEY=%%i
for /f %%i in ('python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"') do set FERNET_KEY=%%i

echo.
echo ================================================
echo  YOUR SECRET KEYS (already saved to .env)
echo ================================================
echo SECRET_KEY=%SECRET_KEY%
echo FERNET_KEY=%FERNET_KEY%
echo ================================================
echo.

REM Create .env file
echo Creating .env file...
(
echo FLASK_ENV=development
echo SECRET_KEY=%SECRET_KEY%
echo AWS_CREDENTIALS_ENCRYPTION_KEY=%FERNET_KEY%
echo MYSQL_HOST=mysql
echo MYSQL_USER=sfluser
echo MYSQL_PASSWORD=sflpass123
echo MYSQL_ROOT_PASSWORD=sflroot123
echo MYSQL_DB=secure_file_storage
echo UPLOAD_DIR=/app/uploads
echo BASE_URL=http://localhost:5000
echo CORS_ORIGINS=http://localhost:3000
echo LOG_LEVEL=INFO
echo LOG_FILE=logs/app.log
) > backend\.env

echo .env file created!
echo.

REM Create required directories
echo Creating directories...
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist static mkdir static

REM Start application
echo Starting application...
docker-compose up --build -d

echo.
echo Waiting for containers to start (30 seconds)...
timeout /t 30 /nobreak > nul

echo.
echo Checking status...
docker-compose ps

echo.
echo ================================================
echo  SETUP COMPLETE!
echo ================================================
echo.
echo  Open these in your browser:
echo  App:     http://localhost:3000
echo  Grafana: http://localhost:3001
echo  API:     http://localhost:5000/health
echo.
echo  Grafana login:
echo  Username: admin
echo  Password: admin123
echo ================================================
echo.
pause
