#!/bin/bash
# setup_buildozer.sh — Установка Buildozer с Python 3.11 для Codespaces
# Запускать: bash setup_buildozer.sh

set -e

echo "=== Установка Python 3.11 через deadsnakes PPA ==="

# Добавляем PPA с Python 3.11
sudo apt update -qq
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update -qq

# Устанавливаем Python 3.11 и все необходимое для сборки
sudo apt install -y python3.11 python3.11-dev python3.11-venv python3.11-distutils

# Системные зависимости для Buildozer
sudo apt install -y git zip unzip openjdk-17-jdk libltdl-dev libffi-dev libssl-dev libtool libtool-bin autoconf automake

echo "=== Установка Buildozer и Cython для Python 3.11 ==="

# Устанавливаем pip для Python 3.11 (если ещё не установлен)
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.11 2>/dev/null || true

# Устанавливаем Buildozer и Cython (игнорируем ошибки с pip)
sudo python3.11 -m pip install buildozer==1.5.0 cython==0.29.36 --ignore-installed 2>/dev/null || \
sudo python3.11 -m pip install buildozer==1.5.0 cython==0.29.36 --break-system-packages 2>/dev/null || \
python3.11 -m pip install --user buildozer==1.5.0 cython==0.29.36

echo "=== Проверка ==="
echo "Python: $(python3.11 --version)"
echo "Buildozer: $(python3.11 -m buildozer --version 2>/dev/null || echo 'check path')"
echo "Java: $(java -version 2>&1 | head -1)"

echo ""
echo "✅ Всё готово! Теперь выполни:"
echo "   python3.11 -m buildozer -v android debug"