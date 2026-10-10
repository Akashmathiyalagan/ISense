@echo off
echo ===================================================
echo Starting ISense Platform in Production Mode
echo ===================================================

echo [1/2] Starting RAG Backend on port 8000...
start "ISense Backend" cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/2] Starting Web Platform on port 5174...
start "ISense Frontend" cmd /k "npm run preview -- --port 5174 --host"

echo Services started successfully!
echo Web Application: http://localhost:5174/
echo Backend & API Docs: http://localhost:8000/docs
pause
