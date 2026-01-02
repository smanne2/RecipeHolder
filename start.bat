@echo off
REM RecipeHolder - Quick Start Script for Windows
REM This script helps you get started with RecipeHolder quickly

echo ========================================
echo   RecipeHolder - Quick Start
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo Docker and Docker Compose are installed
echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo .env file created
) else (
    echo .env file already exists
)
echo.

REM Create data directory
if not exist data (
    echo Creating data directory...
    mkdir data\recipes
    echo Data directory created
) else (
    echo Data directory already exists
)
echo.

REM Build and start containers
echo Building Docker image...
docker-compose build

echo.
echo Starting RecipeHolder...
docker-compose up -d

echo.
echo Waiting for application to start...
timeout /t 5 /nobreak >nul

REM Check if application is running
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo Application may still be starting...
    echo Check logs: docker-compose logs -f recipe-holder
    echo Or visit: http://localhost:8000
) else (
    echo RecipeHolder is running!
    echo.
    echo ========================================
    echo   Setup Complete!
    echo ========================================
    echo.
    echo Access the application:
    echo   Web Interface: http://localhost:8000
    echo   API Docs:      http://localhost:8000/docs
    echo   Health Check:  http://localhost:8000/health
    echo.
    echo Your recipes are stored in: .\data\recipes\
    echo.
    echo Useful commands:
    echo   View logs:     docker-compose logs -f recipe-holder
    echo   Stop app:      docker-compose down
    echo   Restart:       docker-compose restart
    echo.
    echo For more information, see:
    echo   - README.md
    echo   - GETTING_STARTED.md
    echo.
)

pause
