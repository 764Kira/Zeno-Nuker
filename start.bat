@echo off
title Discord Recovery - Installer
color 0A

echo ========================================
echo   Discord Recovery - Setup ^& Start
echo ========================================
echo.

echo [1/2] Installiere Abhaengigkeiten...
pip install discord.py>=2.0 PyQt5>=5.15 aiohttp>=3.8
echo.

echo [2/2] Starte Panel...
echo ========================================
python panel.py

pause
