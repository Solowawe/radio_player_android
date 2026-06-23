[app]

# Название приложения
title = Radio Player

# Пакет (уникальный идентификатор)
package.name = radioplayer

# Домен пакета
package.domain = org.radioplayer

# Версия (числовая) — целое число для buildozer
version = 1

# Версия для отображения (строка)
version.name = 1.0.0

# Главный файл
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf

# Зависимости (pip)
# python3==3.11.5 — фиксируем Python 3.11.5 (совместим с Pyjnius)
requirements = python3==3.11.5,kivy==2.3.0,kivymd==1.1.1,requests,urllib3

# Ориентация экрана
orientation = portrait

# Разрешения Android
android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_AUDIO

# ──────────────────────────────────────────────
# Настройки для Android 12 (API 31)
# ──────────────────────────────────────────────
#
# Android 12 — оптимальная версия для большинства современных устройств.
# API 31 — target SDK для Android 12.
# minapi 21 — минимальная поддержка Android 5.0 (Lollipop).
#
# ╔══════════════════════════════════════════════════════════════╗
# ║  Таблица совместимости API и версий Android                ║
# ╠══════════════════════════════════════════════════════════════╣
# ║  API  | Android  | NDK  | SDK  | minapi | minSDK           ║
# ║───────┼──────────┼──────┼──────┼────────┼──────────────────║
# ║  31   | 12       | 25b  | 31   | 21     | Android 5.0+     ║
# ║  33   | 13       | 25b  | 33   | 21     | Android 5.0+     ║
# ║  34   | 14       | 27b  | 34   | 21     | Android 5.0+     ║
# ║  35   | 15       | 27b  | 35   | 24     | Android 7.0+     ║
# ╚══════════════════════════════════════════════════════════════╝

# API уровень (Android 12, min Android 5.0)
android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 25b
android.gradle_dependencies = androidx.media:media:1.6.0

# python-for-android (p4a)
# Не фиксируем ветку — buildozer использует актуальную версию p4a
# Python 3.11 фиксирован в requirements, p4a подберёт совместимую версию

# Подпись APK
android.allow_backup = true
android.keystore =
android.keystore.alias =

# Иконка (можно заменить своей)
# icon = icon.png

# Название APK файла
android.filename = RadioPlayer

# Архитектуры процессора
# arm64-v8a      — 64-битные ARM (современные телефоны, ~95% устройств)
# armeabi-v7a    — 32-битные ARM (старые телефоны)
# x86_64         — 64-битные Intel (эмуляторы, Chromebook)
# x86            — 32-битные Intel (редко)
#
# Варианты:
#   Только современные:   arm64-v8a
#   Макс. совместимость:  arm64-v8a, armeabi-v7a
#   Всё включая эмулятор: arm64-v8a, armeabi-v7a, x86_64, x86
android.archs = arm64-v8a, armeabi-v7a
android.reduce_png = true
android.enable_androidx = true

# Логи
android.logcat_filters = *:S python:V

# Язык
android.strings = en_US,ru_RU

[buildozer]

# Лог сборки
log_level = 2

# Директория для сборки
build_dir = ./.build

# Директория для бинарников
bin_dir = ./bin

[requirements]
# Дополнительные требования для сборки
# (устанавливаются через pip на хосте)
# Явно указываем Python 3.11, чтобы версия совпадала с requirements
hostpython3 = python3.11
hostpip = pip3

[app:ios]
# iOS настройки (не используются)

[app:windows]
# Windows настройки (не используются)