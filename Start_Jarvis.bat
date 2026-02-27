@echo off
title Jarvis AI Dashboard

echo ==============================================
echo  Starting Jarvis AI - Your Study Buddy...
echo ==============================================
echo.

:: Ask user for model preference to save RAM
cd d:\aibuddy
python choose_brain.py

echo.
echo 1. Waking up the Brain (Ollama)
echo 2. Scanning your Textbooks...
echo 3. Connecting the Voice Engine...
echo.

:: Automatically open the browser to the Jarvis dashboard
start http://127.0.0.1:5000

:: Run the Python backend server
python app.py

pause
