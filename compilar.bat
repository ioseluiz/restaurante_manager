@echo off
echo ========================================================
echo   Compilando Italos Manager con PyInstaller
echo ========================================================
echo.

:: Limpiar carpetas previas si existen para evitar conflictos
if exist build rd /s /q build
if exist dist rd /s /q dist

:: Ejecutar PyInstaller
:: --onedir: Crea una carpeta con el ejecutable y dependencias
:: --windowed: No abre consola al ejecutar (GUI)
:: --name: Nombre del ejecutable final
:: --add-data: Incluye la carpeta de assets (Windows usa ; como separador)
:: --icon: Icono de la aplicacion
pyinstaller --noconfirm --onedir --windowed --name "ItalosManager" ^
    --add-data "assets;assets" ^
    --icon "assets/icons/app.ico" ^
    main.py

echo.
echo ========================================================
echo   Compilacion finalizada. El ejecutable esta en dist/ItalosManager/
echo ========================================================
pause
