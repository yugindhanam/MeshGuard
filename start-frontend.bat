@echo off
title MeshGuard Next.js Frontend
cd /d "%~dp0frontend"
echo Installing dependencies...
call npm install
echo.
echo Starting Next.js dev server on http://localhost:3000 ...
call npm run dev
pause
