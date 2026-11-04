@echo off
title Sistema de Control de Tesis - Biblioteca IUTIRLA
color 0A
echo ========================================================
echo   INICIANDO SISTEMA DE GESTION DE TESIS - IUTIRLA
echo ========================================================
echo Encendiendo servidor local y abriendo interfaz web...

start /b uvicorn main:app --host 127.0.0.1 --port 8000

timeout /t 2 >nul

echo Abriendo el sistema en el navegador de la profesora...
start http://127.0.0.1:8000/static/index.html

echo.
echo ========================================================
echo   ¡SISTEMA ACTIVO! 
echo   La profesora ya puede usar el programa con total normalidad.
echo   (No cierre esta ventana negra mientras la biblioteca esté abierta).
echo ========================================================
pause