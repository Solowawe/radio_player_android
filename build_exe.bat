@echo off
chcp 65001 >nul
title Сборка EXE — Radio Player

echo ============================================
echo   Сборка EXE — Radio Player
echo ============================================
echo.

:: Переходим в папку скрипта
cd /d "%~dp0"

:: Проверка виртуального окружения
if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Создание виртуального окружения...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [!] Ошибка создания виртуального окружения
        pause
        exit /b 1
    )
) else (
    echo [1/4] Виртуальное окружение найдено
)

:: Активация и установка зависимостей
echo [2/4] Установка зависимостей...
call .venv\Scripts\activate.bat

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] Ошибка установки зависимостей
    pause
    exit /b 1
)

:: Установка PyInstaller
pip install pyinstaller
if %errorlevel% neq 0 (
    echo [!] Ошибка установки PyInstaller
    pause
    exit /b 1
)

:: Сборка EXE
echo [3/4] Сборка EXE (это может занять несколько минут)...
pyinstaller --onefile --windowed --name "RadioPlayer" ^
    --hidden-import PySide6.QtMultimedia ^
    --hidden-import PySide6.QtWebEngineWidgets ^
    --hidden-import PySide6.QtWebEngineCore ^
    --hidden-import PySide6.QtNetwork ^
    --exclude-module PySide6.QtBluetooth ^
    --exclude-module PySide6.Qt3DCore ^
    --exclude-module PySide6.Qt3DAnimation ^
    --exclude-module PySide6.Qt3DExtras ^
    --exclude-module PySide6.Qt3DInput ^
    --exclude-module PySide6.Qt3DLogic ^
    --exclude-module PySide6.Qt3DRender ^
    --exclude-module PySide6.QtCharts ^
    --exclude-module PySide6.QtDataVisualization ^
    --exclude-module PySide6.QtGraphs ^
    --exclude-module PySide6.QtHelp ^
    --exclude-module PySide6.QtHttpServer ^
    --exclude-module PySide6.QtLocation ^
    --exclude-module PySide6.QtMultimediaWidgets ^
    --exclude-module PySide6.QtNfc ^
    --exclude-module PySide6.QtOpenGL ^
    --exclude-module PySide6.QtOpenGLWidgets ^
    --exclude-module PySide6.QtPdf ^
    --exclude-module PySide6.QtPdfWidgets ^
    --exclude-module PySide6.QtPositioning ^
    --exclude-module PySide6.QtPrintSupport ^
    --exclude-module PySide6.QtQml ^
    --exclude-module PySide6.QtQuick ^
    --exclude-module PySide6.QtQuick3D ^
    --exclude-module PySide6.QtRemoteObjects ^
    --exclude-module PySide6.QtSensors ^
    --exclude-module PySide6.QtSerialBus ^
    --exclude-module PySide6.QtSerialPort ^
    --exclude-module PySide6.QtShaderTools ^
    --exclude-module PySide6.QtSpatialAudio ^
    --exclude-module PySide6.QtSql ^
    --exclude-module PySide6.QtSvg ^
    --exclude-module PySide6.QtSvgWidgets ^
    --exclude-module PySide6.QtTest ^
    --exclude-module PySide6.QtTextToSpeech ^
    --exclude-module PySide6.QtUiTools ^
    --exclude-module PySide6.QtWebChannel ^
    --exclude-module PySide6.QtWebSockets ^
    --exclude-module PySide6.QtXml ^
    --exclude-module PySide6.QtDBus ^
    main.py

if %errorlevel% neq 0 (
    echo [!] Ошибка сборки EXE
    pause
    exit /b 1
)

:: Готово
echo [4/4] Сборка завершена!
echo.
echo ============================================
echo   EXE создан: dist\RadioPlayer.exe
echo ============================================
echo.
for %%I in ("dist\RadioPlayer.exe") do (
    set SIZE=%%~zI
)
echo Размер: %SIZE% байт (%SIZE:~0,-6% МБ)
echo.
echo Чтобы запустить: dist\RadioPlayer.exe
echo.

pause