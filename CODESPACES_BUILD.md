# Сборка APK через GitHub Codespaces

## Шаг 1. Создать репозиторий на GitHub

1. Открой [github.com](https://github.com) и войди в аккаунт
2. Нажми зелёную кнопку **"New"** (или **"Create repository"**)
3. Назови репозиторий, например: `radio-player-android`
4. Оставь **Public** (или Private — без разницы)
5. Нажми **"Create repository"**

## Шаг 2. Загрузить файлы проекта

1. На странице репозитория нажми **"Add file" → "Upload files"**
2. Перетащи ZIP-архив [`radio_player_android.zip`](radio_player_android.zip) в окно браузера
3. Нажми **"Commit changes"**

## Шаг 3. Открыть Codespaces

1. На странице репозитория нажми зелёную кнопку **"Code"**
2. Выбери вкладку **"Codespaces"**
3. Нажми **"Create codespace on main"**
4. Подожди 1-2 минуты — откроется онлайн-VS Code

## Шаг 4. Установить Python 3.11 и Buildozer

**Важно:** В Codespaces по умолчанию Python 3.12, который несовместим с Pyjnius. Нужно использовать Python 3.11.

В терминале Codespaces выполни:

```bash
# Делаем скрипт исполняемым и запускаем
chmod +x setup_buildozer.sh
bash setup_buildozer.sh
```

Или вручную:

```bash
# Установка Python 3.11
sudo apt update -qq
sudo apt install -y python3.11 python3.11-dev python3.11-venv

# Создаём виртуальное окружение с Python 3.11
python3.11 -m venv buildozer_env
source buildozer_env/bin/activate

# Системные зависимости
sudo apt install -y git zip unzip openjdk-17-jdk libltdl-dev libffi-dev libssl-dev libtool libtool-bin autoconf automake

# Buildozer и Cython
pip install --upgrade pip
pip install buildozer==1.5.0 cython==0.29.36

# Проверка
python --version   # должно быть Python 3.11.x
buildozer --version
java -version
```

## Шаг 5. Собрать APK

```bash
# Убедись, что виртуальное окружение активно (должно быть (buildozer_env) в начале строки)
# Если нет — выполни: source buildozer_env/bin/activate

# Сборка (15-30 минут)
yes | buildozer -v android debug
```

## Шаг 6. Скачать APK

После сборки APK будет в папке `bin/`:

```bash
# Проверить, что APK создан
ls -la bin/*.apk
```

Чтобы скачать:
1. В боковой панели Codespaces (слева) открой папку `bin/`
2. Найди файл `RadioPlayer-1.0.0-*-debug.apk`
3. Нажми правой кнопкой → **Download**

## Шаг 7. Установить на эмулятор/телефон

1. Перенеси APK на устройство (через USB, Telegram, Google Drive)
2. Открой файл APK на телефоне
3. Подтверди установку из неизвестных источников

---

## Если сборка упадёт с ошибкой

### Ошибка "undeclared name not builtin: long" (Pyjnius + Python 3.12)

Это значит, что ты используешь Python 3.12. Решение:
```bash
# Установи Python 3.11 и создай виртуальное окружение
sudo apt install -y python3.11 python3.11-dev python3.11-venv
python3.11 -m venv buildozer_env
source buildozer_env/bin/activate
pip install buildozer==1.5.0 cython==0.29.36
# После этого запусти сборку снова
```

### Ошибка "java not found"

```bash
sudo apt install -y openjdk-17-jdk
```

### Ошибка "No space left on device"

Codespaces даёт 15 ГБ. Если место кончилось:
```bash
# Очистить кэш Buildozer
rm -rf ~/.buildozer
```

### Другие ошибки

Скопируй текст ошибки и покажи мне — разберёмся.