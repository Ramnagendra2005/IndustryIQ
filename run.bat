@echo off
REM ============================================================================
REM  IndustryIQ - One-Command Launcher (Windows)
REM  Usage:
REM    run.bat          -  Build everything and serve on http://localhost:8000
REM    run.bat dev      -  Backend on :8000 + Vite dev server on :5173 (hot reload)
REM ============================================================================

cd /d "%~dp0"

REM --- Python dependencies ---------------------------------------------------
echo [1/3] Installing backend dependencies...
python -m pip install -q -r backend\requirements.txt 2>nul

REM --- Seed + Corpus ---------------------------------------------------------
echo [2/3] Building seed + corpus data...
python backend\scripts\build_seed.py
python backend\scripts\generate_corpus.py

REM --- Frontend + Backend ----------------------------------------------------
if "%~1"=="dev" goto :dev_mode

:prod_mode
echo [3/3] Building frontend and starting production server...
cd frontend
call npm install --silent
call npm run build
cd ..
echo.
echo ============================================
echo   IndustryIQ running on http://localhost:8000
echo   Press Ctrl+C to stop
echo ============================================
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
goto :eof

:dev_mode
echo [3/3] Starting dev servers (backend :8000 + frontend :5173)...
echo.
echo ============================================
echo   Backend  -  http://localhost:8000
echo   Frontend -  http://localhost:5173
echo   Press Ctrl+C to stop
echo ============================================
echo.

REM Install frontend deps first
cd frontend
call npm install --silent
cd ..

REM Start backend in a new window, frontend in current window
start "IndustryIQ Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.app.main:app --reload --port 8000"
cd frontend
call npm run dev
