@echo off
title Predium - Plataforma de Inteligencia Inmobiliaria
setlocal

cd /d "%~dp0"

echo ========================================================
echo Iniciando Predium (Backend API + Frontend Web)
echo ========================================================
echo.

:: Limpieza previa de puertos para evitar procesos zombies
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo [CLEANUP] Liberando puerto 8000 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo [CLEANUP] Liberando puerto 3000 (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en .venv.
    pause
    exit /b 1
)

echo [1/3] Levantando Backend API con Auto-Reload y Logs en vivo...
start "Predium Backend API" cmd /k ".\.venv\Scripts\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Esperando inicializacion del backend...
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
