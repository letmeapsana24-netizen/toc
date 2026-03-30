@echo off
echo Starting TuringLab AI Application...
echo.

start "TuringLab Backend" cmd /c "cd backend && node server.js"
echo Backend started on http://localhost:3000

echo.
echo Launching Frontend...
start "" "frontend\index.html"

echo.
echo Application is running!
pause
