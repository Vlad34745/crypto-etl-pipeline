@echo off
title Crypto ETL Pipeline Automation
echo ===================================================
echo [STARTING] Launching Crypto Telemetry Pipeline...
echo ===================================================
echo.

:: 1. Активація віртуального середовища venv
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

:: 2. Запуск скрипту всередині правильного середовища
python crypto_automation.py

echo.
echo ===================================================
echo [SUCCESS] Pipeline executed. Excel updated cleanly!
echo ===================================================
echo.
pause