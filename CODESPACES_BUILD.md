# Сборка APK через GitHub Codespaces

## Шаг 1. Создать репозиторий на GitHub

1. Открой [github.com](https://github.com) и войди в аккаунт
2. Нажми зелёную кнопку **"New"** (или **"Create repository"**)
3. Назови репозиторий, например: `radio-player-android`
4. Оставь **Public** (или Private — без разницы)
5. Нажми **"Create repository"**

## Шаг 2. Загрузить файлы проекта

После создания репозитория у тебя будет страница с инструкциями. Сделай так:

### Вариант A — через веб-интерфейс (проще всего):

1. На странице репозитория нажми **"Add file" → "Upload files"**
2. Перетащи ZIP-архив [`radio_player_android.zip`](radio_player_android.zip) в окно браузера
3. Нажми **"Commit changes"**

### Вариант B — через Git (если знаком с Git):

```bash
# Клонируем репозиторий
git clone https://github.com/ТВОЙ_ЛОГИН/radio-player-android.git
cd radio-player-android

# Копируем файлы из проекта
cp /путь/к/radio_player/android/* .

# Заливаем на GitHub
git add .
git commit -m "Initial commit"
git push
```

## Шаг 3. Открыть Codespaces

1. На странице репозитория нажми зелёную кнопку **"Code"**
2. Выбери вкладку **"Codespaces"**
3. Нажми **"Create codespace on main"**
4. Подожди 1-2 минуты — откроется онлайн-VS Code

## Шаг 4. Установить Buildozer

В терминале Codespaces (внизу) выполни по очереди:

```bash
# Обновление пакетов
sudo apt update -qq

# Установка системных зависимостей
sudo apt install -y python3-pip git zip unzip openjdk-17-jdk libltdl-dev libffi-dev libssl-dev libtool libtool-bin autoconf automake

# Установка Buildozer
pip install buildozer==1.5.0 cython

# Проверка
buildozer --version
java -version
python3 --version
```

## Шаг 5. Собрать APK

```bash
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

Или через терминал:
```bash
# Установить gh CLI (если не установлен)
# Или просто скачай через веб-интерфейс Codespaces
```

## Шаг 7. Установить на эмулятор/телефон

1. Перенеси APK на устройство (через USB, Telegram, Google Drive)
2. Открой файл APK на телефоне
3. Подтверди установку из неизвестных источников

---

## Если сборка упадёт с ошибкой

### Ошибка "Python 3.14 not compatible with Kivy 2.3.0"

В [`buildozer.spec`](buildozer.spec) уже прописано:
```
p4a.branch = v2024.01.21
requirements = python3==3.11.5,kivy==2.3.0,kivymd==1.1.1,requests,urllib3
```

Если ошибка всё равно появляется — проверь, что эти строки не закомментированы.

### Ошибка "java not found"

Выполни заново:
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