# Radio Player для Android 📻

Нативное Android-приложение радио-плеера на Kivy + KivyMD.

## Возможности

- **Radio Record**: 60+ станций без рекламы (прямой эфир через API)
- **Локальные файлы**: воспроизведение аудио с телефона
- **Ссылки**: вставка прямой ссылки на аудио-поток
- **Material Design**: тёмная тема, современный интерфейс
- **Без рекламы**: никаких встроенных баннеров
- **Маленький размер**: APK ~8-15MB

## Структура проекта

```
android/
├── main.py              # Главный файл приложения (Kivy + KivyMD)
├── music_player.py      # Ядро плеера (Track, MusicPlayer, Radio Record)
├── buildozer.spec       # Конфиг для сборки APK
├── requirements.txt     # Зависимости
└── README.md            # Этот файл
```

---

## Сборка APK на Windows (без Docker, без WSL)

На чистой Windows собрать APK напрямую нельзя — Buildozer требует Linux.
Единственный способ без установки дополнительных программ — **Google Colab** (всё делается через браузер).

### Пошаговая инструкция

**Шаг 1.** Открой [Google Colab](https://colab.research.google.com/)

**Шаг 2.** Нажми **"Новый ноутбук"** (New Notebook)

**Шаг 3.** Скопируй и вставь этот код в первую ячейку, нажми `Shift+Enter`:

```python
# Установка Buildozer
!apt update
!apt install -y python3-pip git zip unzip openjdk-17-jdk
!pip install buildozer cython
print("✅ Buildozer установлен!")
```

**Шаг 4.** Нажми `+ Код`, вставь и выполни:

```python
# Загрузка проекта
# 1. Нажми на иконку 📁 (папка) слева
# 2. Нажми на значок загрузки (↑)
# 3. Выбери папку radio_player/android/ (или zip-архив с ней)
# 4. Дождись загрузки

import zipfile, os
from google.colab import files

uploaded = files.upload()
for fn in uploaded.keys():
    if fn.endswith('.zip'):
        with zipfile.ZipFile(fn, 'r') as zf:
            zf.extractall()
        os.remove(fn)
        print(f"✅ Распакован: {fn}")
```

**Шаг 5.** Нажми `+ Код`, вставь и выполни:

```python
# Сборка APK (15-30 минут)
import os

# Определяем, где лежит buildozer.spec
if os.path.exists('radio_player/android/buildozer.spec'):
    build_dir = 'radio_player/android'
elif os.path.exists('buildozer.spec'):
    build_dir = '.'
else:
    build_dir = None
    print("❌ buildozer.spec не найден!")
    print("   Содержимое текущей папки:", os.listdir('.'))

if build_dir:
    !cd {build_dir} && buildozer android debug 2>&1
    print("✅ Сборка завершена!")
```

**Шаг 6.** Нажми `+ Код`, вставь и выполни:

```python
# Скачать APK на компьютер
from google.colab import files
import glob
import os

# Buildozer кладёт APK в bin/ относительно buildozer.spec
for possible_dir in ['radio_player/android/bin', 'bin']:
    if os.path.exists(possible_dir):
        apk_files = glob.glob(f'{possible_dir}/*.apk')
        if apk_files:
            for apk in apk_files:
                files.download(apk)
            print(f"✅ Скачивается {len(apk_files)} APK: {[os.path.basename(f) for f in apk_files]}")
            break
else:
    print("❌ APK не найден. Проверь логи сборки в шаге 5.")
    # Диагностика
    for d in ['radio_player/android/bin', 'radio_player/android', 'bin', '.']:
        if os.path.exists(d):
            items = os.listdir(d)
            print(f"  Содержимое {d}: {items}")
            # Если есть вложенные папки, заглянем в них
            for item in items:
                item_path = os.path.join(d, item)
                if os.path.isdir(item_path):
                    print(f"    {item}/: {os.listdir(item_path)}")
```

Готово! APK скачается на твой компьютер.

---

## Тестирование на десктопе (Windows)

```cmd
cd d:\prjs\smart\cursor\nt2\radio_player\android
pip install -r requirements.txt
python main.py
```

## Зависимости

- **Kivy 2.3.0** — графический движок
- **KivyMD 1.1.1** — Material Design компоненты
- **requests** — HTTP-запросы к API Radio Record
- **SoundLoader** (встроен в Kivy) — воспроизведение аудио

## Примечания

- На Android воспроизведение потокового аудио (Radio Record) работает через `SoundLoader.load(url)`
- Для доступа к локальным файлам на Android 13+ требуется разрешение `READ_MEDIA_AUDIO`
- Для выбора папок на Android используется Storage Access Framework (SAF)