@echo off
title Zeno Solutions
color 0A

echo ========================================
echo   Zeno Solutions - Setup ^& Start
echo ========================================
echo.

echo [1/2] Installiere Abhaengigkeiten...
pip install discord.py>=2.0 PyQt5>=5.15 aiohttp>=3.8
echo.

echo [2/2] Starte Panel...
echo ========================================
python panel.py

pause

