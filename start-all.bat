@echo off
title MeshGuard - Start All
echo Launching MeshGuard Backend and Frontend...
echo.
start "MeshGuard Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak > nul
start "MeshGuard Frontend" cmd /k "cd /d %~dp0frontend && npm install && npm run dev"
echo.
echo Both servers are starting:
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo.
pause
