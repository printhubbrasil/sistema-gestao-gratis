@echo off
title Sistema de Gestão — Gráfica
cd /d "%~dp0"
echo.
echo  Iniciando sistema...
echo.
pip install flask --quiet 2>nul
python app.py
pause
