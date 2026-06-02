@echo off
echo Starting AgroConnect...

:: Start Action Server
start "Action Server" cmd /k "cd /d "C:\Users\win 10\OneDrive\Desktop\AgroConnect" && rasa_env\Scripts\activate && rasa run actions --port 5055"

:: Wait 5 seconds
timeout /t 5 /nobreak

:: Start Rasa Server
start "Rasa Server" cmd /k "cd /d "C:\Users\win 10\OneDrive\Desktop\AgroConnect" && rasa_env\Scripts\activate && rasa run --enable-api --cors "*" --port 5005"

:: Wait 15 seconds for Rasa to load
timeout /t 15 /nobreak

:: Start Backend
start "Backend" cmd /k "cd /d "C:\Users\win 10\OneDrive\Desktop\AgroConnect\backend" && uvicorn main:app --reload --port 8000"

:: Wait 3 seconds
timeout /t 3 /nobreak

:: Start Frontend
start "Frontend" cmd /k "cd /d "C:\Users\win 10\OneDrive\Desktop\AgroConnect\frontend" && npm run dev"

:: Wait 5 seconds then open browser
timeout /t 5 /nobreak
start http://localhost:5173