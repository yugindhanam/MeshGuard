@echo off
title MeshGuard FastAPI Backend
cd /d "%~dp0"
echo Starting MeshGuard FastAPI backend on http://localhost:8000 ...
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
pause
