#!/bin/bash
# setup_buildozer.sh — Установка Buildozer с Python 3.11 для Codespaces
# Запускать: bash setup_buildozer.sh

set -e

echo "=== Установка Python 3.11 ==="

# Устанавливаем Python 3.11
sudo apt update -qq
sudo apt install -y python3.11 python3.11-dev python3.11-venv

# Создаём виртуальное окружение с Python 3.11
python3.11 -m venv buildozer_env
source buildozer_env/bin/activate

echo "=== Установка системных зависимостей ==="
sudo apt install -y git zip unzip openjdk-17-jdk libltdl-dev libffi-dev libssl-dev libtool libtool-bin autoconf automake

echo "=== Установка Buildozer и Cython ==="
pip install --upgrade pip
pip install buildozer==1.5.0 cython==0.29.36

echo "=== Проверка ==="
echo "Python: $(python --version)"
echo "Buildozer: $(buildozer --version)"
echo "Java: $(java -version 2>&1 | head -1)"

echo ""
echo "✅ Всё готово! Теперь выполни:"
echo "   source buildozer_env/bin/activate"
echo "   yes | buildozer -v android debug"