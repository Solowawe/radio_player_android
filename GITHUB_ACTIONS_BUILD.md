# 📦 Сборка APK через GitHub Actions

Этот проект использует **GitHub Actions** для автоматической сборки APK-файла Radio Player.

## 🔄 Как это работает

При каждом пуше в ветку `main` или `master`, GitHub автоматически:
1. Запускает виртуальную машину с Ubuntu
2. Устанавливает Python 3.11, Java 17, Buildozer и все зависимости
3. Собирает APK (30–60 минут)
4. Загружает готовый APK как артефакт сборки

## 📱 Как скачать APK

### Способ 1: Автоматически после пуша

1. Сделай пуш в репозиторий:
   ```bash
   git add .
   git commit -m "Update Radio Player"
   git push
   ```

2. Открой репозиторий на GitHub → вкладка **Actions**

3. Найди последний запуск workflow **"Build Radio Player APK"**

4. Нажми на него → внизу страницы увидишь раздел **Artifacts**

5. Нажми **"RadioPlayer-APK-..."** — скачается ZIP с APK внутри

### Способ 2: Ручной запуск

1. Открой репозиторий на GitHub → вкладка **Actions**

2. Слева выбери **"Build Radio Player APK"**

3. Нажми кнопку **"Run workflow"** (справа)

4. Выбери параметры:
   - **Android API level**: `33` (рекомендуется для Android 13)
   - **Minimum Android API level**: `21` (Android 5.0+)

5. Нажми **"Run workflow"** и жди 30–60 минут

6. После завершения скачай APK из **Artifacts**

## ⚙️ Структура файлов для сборки

```
radio_player/android/
├── main.py              # Главный файл приложения
├── music_player.py      # Ядро плеера
├── buildozer.spec       # Конфигурация Buildozer
├── requirements.txt     # Зависимости Python
└── README.md            # Документация

.github/workflows/
└── build-apk.yml        # GitHub Actions workflow
```

## 🛠 Настройка под свою версию Android

В файле [`buildozer.spec`](radio_player/android/buildozer.spec) можно изменить:

| Параметр | Значение | Описание |
|----------|----------|----------|
| `android.api` | `31`–`35` | Целевая версия Android |
| `android.minapi` | `21`–`24` | Минимальная версия Android |
| `android.ndk` | `25b`–`27b` | Версия NDK |
| `android.archs` | `arm64-v8a, armeabi-v7a` | Архитектуры процессора |

## ❗ Возможные проблемы

### Сборка падает с ошибкой "No space left on device"
GitHub Actions даёт ~14 ГБ дискового пространства. В workflow уже добавлена очистка, но если не хватает:
- Уменьши `android.archs` до `arm64-v8a` (только 64-битные устройства)

### Сборка длится дольше 2 часов
Workflow имеет таймаут 120 минут. Если не укладываешься:
- Уменьши количество архитектур в `android.archs`
- Используй `p4a.branch = develop` (уже установлено)

### Ошибка компиляции Kivy
Если сборка падает с ошибками в C-файлах Kivy — это проблема совместимости Python и Kivy. В workflow используется Python 3.11, который совместим с Kivy 2.3.0.

## 📋 Альтернативные способы сборки

- **Google Colab**: [`build_apk_colab.ipynb`](radio_player/android/build_apk_colab.ipynb) — сборка через браузер
- **GitHub Codespaces**: [`CODESPACES_BUILD.md`](radio_player/android/CODESPACES_BUILD.md) — сборка в онлайн-VS Code