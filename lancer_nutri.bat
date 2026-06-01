@echo off
cd /d C:\NutriTracker
python main.py
if %errorlevel% neq 0 pause
