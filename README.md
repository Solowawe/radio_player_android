# 📻 Radio Player APK

Сборка APK радио-плеера для Android через GitHub Actions.

## 📱 Возможности

- **Radio Record**: 60+ станций без рекламы
- **Избранные станции**: сохраняются между запусками
- **Автоматическое переподключение**: при обрыве потока
- **Локальные аудиофайлы**: воспроизведение с телефона
- **Воспроизведение по ссылке**: прямая ссылка на аудио
- **Материальный дизайн**: KivyMD

## 🔄 Сборка через GitHub Actions

### Автоматически
При каждом пуше в ветку `main` или `master`:

```bash
git add .
git commit -m "Update Radio Player"
git push
```

1. Открой репозиторий на GitHub → вкладка **Actions**
2. Найди последний запуск **"Build Radio Player APK"**
3. Внизу страницы — раздел **Artifacts**
4. Скачай **RadioPlayer-APK-...** (ZIP с APK внутри)

### Вручную
1. Открой репозиторий → **Actions** → **"Build Radio Player APK"**
2. Нажми **"Run workflow"**
3. Выбери параметры:
   - **Android API level**: `33` (Android 13, рекомендуется)
   - **Minimum Android API level**: `21` (Android 5.0+)
4. Жди 30–60 минут
5. Скачай APK из **Artifacts**

## ⚙️ Структура файлов

```
radio_player_apk/
├── .github/workflows/
│   └── build-apk.yml     # GitHub Actions workflow
├── main.py               # Главный файл приложения
├── music_player.py       # Ядро плеера
├── buildozer.spec        # Конфигурация Buildozer
├── requirements.txt      # Зависимости Python
└── README.md             # Этот файл
```

## 🛠 Настройка

В файле [`buildozer.spec`](buildozer.spec) можно изменить:

| Параметр | Значение | Описание |
|----------|----------|----------|
| `android.api` | `31`–`35` | Целевая версия Android |
| `android.minapi` | `21`–`24` | Минимальная версия Android |
| `android.ndk` | `25b`–`27b` | Версия NDK |
| `android.archs` | `arm64-v8a, armeabi-v7a` | Архитектуры процессора |

## ❗ Возможные проблемы

### Нет звука после установки
Проверь файл `/sdcard/radio_player_crash.log` на телефоне — туда пишутся все ошибки.

### Сборка падает с "No space left on device"
GitHub Actions даёт ~14 ГБ дискового пространства. Уменьши `android.archs` до `arm64-v8a`.

### Сборка длится дольше 2 часов
Workflow имеет таймаут 120 минут. Уменьши количество архитектур в `android.archs`.

## 📋 Альтернативные способы сборки

- **Google Colab**: [`build_apk_colab.ipynb`](android/build_apk_colab.ipynb) — сборка через браузер
- **GitHub Codespaces**: [`CODESPACES_BUILD.md`](android/CODESPACES_BUILD.md) — сборка в онлайн-VS Code