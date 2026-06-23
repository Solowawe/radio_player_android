@echo off
chcp 65001 >nul
REM Создать ZIP-архив для загрузки в Google Colab
REM Запускать из папки radio_player\android\

echo Создание архива radio_player_android.zip...
cd /d "%~dp0"

if exist radio_player_android.zip del radio_player_android.zip

powershell -Command ^
  "Compress-Archive -Path '%~dp0buildozer.spec', '%~dp0main.py', '%~dp0music_player.py', '%~dp0requirements.txt', '%~dp0README.md', '%~dp0build_apk_colab.ipynb' -DestinationPath '%~dp0radio_player_android.zip' -Force"

echo ✅ Архив создан: radio_player_android.zip
echo.
echo Размер:
dir radio_player_android.zip
pause