@echo off
title Predium - Plataforma de Inteligencia Inmobiliaria
setlocal

cd /d "%~dp0"

echo ========================================================
echo Iniciando Predium (Backend API + Frontend Web)
echo ========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en .venv.
    echo Asegurate de crearlo e instalar las dependencias con:
    echo   python -m venv .venv
    echo   .\.venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [INFO] Instalando dependencias de frontend por primera vez...
    cd frontend
    call npm install
    cd ..
)

echo [1/3] Levantando Backend API en http://127.0.0.1:8000 ...
start "Predium Backend API" cmd /k ".\.venv\Scripts\python.exe main.py visor --no-browser"

echo [2/3] Esperando inicio del servidor backend...
timeout /t 3 /nobreak >nul

echo [3/3] Levantando Frontend (React + Vite) en http://localhost:3000 ...
start "Predium Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo Predium se esta ejecutando.
echo   - Frontend: http://localhost:3000
echo   - Backend:  http://127.0.0.1:8000
echo   - Docs API: http://127.0.0.1:8000/docs
echo ========================================================
echo.

timeout /t 2 /nobreak >nul
start http://localhost:3000

exit
