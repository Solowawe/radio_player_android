"""
music_player_gui.py — GUI музыкального плеера на PySide6.

Возможности:
  - Воспроизведение локальных аудиофайлов (mp3, wav, ogg, flac, m4a)
  - Загрузка плейлистов .m3u / .m3u8
  - Онлайн-поиск через VK Музыка (если доступен)
  - Встроенный веб-интерфейс Radio Record (https://www.radiorecord.ru/)
  - Прямой эфир Radio Record без рекламы (через API)
  - Вставка прямой ссылки на аудио
  - Drag & drop файлов и папок
  - Горячие клавиши: Space (play/pause), ←/→ (prev/next)
"""

import logging
import os

# Подавляем шумные сообщения Chromium/QtWebEngine (WebGL blocklist, GPU и т.д.)
os.environ["QT_LOGGING_RULES"] = (
    "qt.webengine.context=true\n"
    "qt.webengine.gpu=false\n"
    "chromium.gpu=false\n"
    "*.debug=false\n"
)

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QLabel,
    QSlider, QApplication, QFrame, QFileDialog, QMenu,
    QMessageBox, QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QUrl
from PySide6.QtGui import (
    QFont, QIcon, QPixmap, QAction, QDragEnterEvent, QDropEvent,
    QKeyEvent, QShortcut, QKeySequence,
)

from music_player import MusicPlayer, Track

logger = logging.getLogger(__name__)

# Попытка импорта QtWebEngine для встроенного браузера
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineProfile
    from PySide6.QtWebEngineWidgets import QWebEngineSettings

    # Отключаем WebGL и другие GPU-функции, чтобы избежать ошибок blocklist
    _web_profile = QWebEngineProfile.defaultProfile()
    _web_settings = _web_profile.settings()
    _web_settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    _web_settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, False)
    _web_settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, False)
    _web_settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
    _web_settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    logger.warning("QtWebEngine не установлен. Radio Record будет открываться во внешнем браузере.")


class MusicPlayerGUI(QWidget):
    """
    Компактный GUI музыкального плеера.

    Можно встроить в другое окно или запустить как отдельное приложение.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._player = MusicPlayer(self)
        self._current_track: Optional[Track] = None
        self._search_query: str = ''
        self._record_mode: bool = False  # True = показан Radio Record
        self._all_record_tracks: list[Track] = []  # полный список станций Radio Record
        self._showing_favorites: bool = False      # показано только избранное

        self._setup_ui()
        self._connect_signals()

        # Таймер для обновления ползунка позиции
        self._position_timer = QTimer(self)
        self._position_timer.setInterval(500)
        self._position_timer.timeout.connect(self._update_position_slider)

        # Горячие клавиши
        self._setup_shortcuts()

        # Включить drag & drop
        self.setAcceptDrops(True)

    def _setup_shortcuts(self):
        """Настройка горячих клавиш."""
        # Space — play/pause
        self._shortcut_play = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self._shortcut_play.activated.connect(self._on_play_pause)

        # → — следующий трек
        self._shortcut_next = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self._shortcut_next.activated.connect(self._player.play_next)

        # ← — предыдущий трек
        self._shortcut_prev = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self._shortcut_prev.activated.connect(self._player.play_prev)

        # Ctrl+O — открыть папку
        self._shortcut_folder = QShortcut(QKeySequence("Ctrl+O"), self)
        self._shortcut_folder.activated.connect(self._on_open_folder)

        # Ctrl+L — загрузить плейлист
        self._shortcut_playlist = QShortcut(QKeySequence("Ctrl+L"), self)
        self._shortcut_playlist.activated.connect(self._on_load_playlist)

    def _setup_ui(self):
        """Создание интерфейса."""
        self.setWindowTitle("Музыкальный плеер")
        self.setMinimumSize(480, 560)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 12px;
                color: #cdd6f4;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
            QPushButton {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 16px;
                color: #cdd6f4;
                font-size: 13px;
                min-width: 36px;
            }
            QPushButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
            QPushButton:pressed {
                background-color: #585b70;
            }
            QPushButton#playBtn {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
                min-width: 60px;
            }
            QPushButton#playBtn:hover {
                background-color: #b4d0fb;
            }
            QPushButton#folderBtn {
                background-color: #a6e3a1;
                color: #1e1e2e;
            }
            QPushButton#folderBtn:hover {
                background-color: #b8f0b4;
            }
            QPushButton#recordBtn {
                background-color: #f9e2af;
                color: #1e1e2e;
            }
            QPushButton#recordBtn:hover {
                background-color: #fceeb8;
            }
            QPushButton#recordBtn:checked {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
            QPushButton#favBtn {
                background-color: #f5c2e7;
                color: #1e1e2e;
            }
            QPushButton#favBtn:hover {
                background-color: #f8d4ed;
            }
            QPushButton#favBtn:checked {
                background-color: #f9e2af;
                color: #1e1e2e;
            }
            QListWidget {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
                border-bottom: 1px solid #313244;
            }
            QListWidget::item:hover {
                background-color: #313244;
            }
            QListWidget::item:selected {
                background-color: #45475a;
                color: #cdd6f4;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #313244;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #89b4fa;
                border-radius: 2px;
            }
            QLabel#trackLabel {
                font-size: 14px;
                font-weight: bold;
                color: #cdd6f4;
            }
            QLabel#timeLabel {
                font-size: 11px;
                color: #6c7086;
            }
            QLabel#statusLabel {
                font-size: 11px;
                color: #6c7086;
            }
            QLabel#radioMetaLabel {
                font-size: 13px;
                color: #a6e3a1;
                font-weight: bold;
                padding: 4px 8px;
                background-color: #313244;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # ── Верхняя панель: поиск + кнопки ──
        top_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍  Поиск в VK Музыке...")
        self._search_input.returnPressed.connect(self._on_search)

        self._search_btn = QPushButton("🔍")
        self._search_btn.setToolTip("Искать в VK Музыке")
        self._search_btn.clicked.connect(self._on_search)

        self._folder_btn = QPushButton("📁")
        self._folder_btn.setObjectName("folderBtn")
        self._folder_btn.setToolTip("Открыть папку с музыкой (Ctrl+O)")
        self._folder_btn.clicked.connect(self._on_open_folder)

        self._playlist_btn = QPushButton("📋")
        self._playlist_btn.setToolTip("Загрузить плейлист .m3u (Ctrl+L)")
        self._playlist_btn.clicked.connect(self._on_load_playlist)

        self._record_btn = QPushButton("📻")
        self._record_btn.setObjectName("recordBtn")
        self._record_btn.setCheckable(True)
        self._record_btn.setToolTip("Radio Record — встроенный веб-интерфейс (авторизация, избранное)")
        self._record_btn.clicked.connect(self._on_toggle_record)

        self._live_btn = QPushButton("📡")
        self._live_btn.setToolTip("Прямой эфир Radio Record — без рекламы, через API")
        self._live_btn.clicked.connect(self._on_load_record_live)

        self._fav_btn = QPushButton("⭐")
        self._fav_btn.setObjectName("favBtn")
        self._fav_btn.setCheckable(True)
        self._fav_btn.setToolTip("Избранные станции Radio Record")
        self._fav_btn.clicked.connect(self._on_show_favorites)

        top_layout.addWidget(self._search_input, stretch=1)
        top_layout.addWidget(self._search_btn)
        top_layout.addWidget(self._folder_btn)
        top_layout.addWidget(self._playlist_btn)
        top_layout.addWidget(self._record_btn)
        top_layout.addWidget(self._live_btn)
        top_layout.addWidget(self._fav_btn)
        layout.addLayout(top_layout)

        # ── Информация о текущем треке ──
        self._track_label = QLabel("🎵  Нет трека")
        self._track_label.setObjectName("trackLabel")
        self._track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._track_label)

        # ── Метаданные радио-потока (название трека/исполнитель) ──
        radio_meta_layout = QHBoxLayout()
        radio_meta_layout.setSpacing(4)

        self._radio_meta_label = QLabel("")
        self._radio_meta_label.setObjectName("radioMetaLabel")
        self._radio_meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._radio_meta_label.setWordWrap(True)
        self._radio_meta_label.hide()  # скрыт, пока нет метаданных

        self._copy_btn = QPushButton("📋")
        self._copy_btn.setToolTip("Копировать название трека")
        self._copy_btn.setFixedWidth(36)
        self._copy_btn.clicked.connect(self._on_copy_track_name)
        self._copy_btn.hide()

        radio_meta_layout.addWidget(self._radio_meta_label, stretch=1)
        radio_meta_layout.addWidget(self._copy_btn)
        layout.addLayout(radio_meta_layout)

        # ── Ползунок позиции ──
        self._position_slider = QSlider(Qt.Orientation.Horizontal)
        self._position_slider.setRange(0, 0)
        self._position_slider.sliderMoved.connect(self._player.seek)
        layout.addWidget(self._position_slider)

        # ── Время ──
        time_layout = QHBoxLayout()
        self._time_current = QLabel("0:00")
        self._time_current.setObjectName("timeLabel")
        self._time_total = QLabel("0:00")
        self._time_total.setObjectName("timeLabel")
        time_layout.addWidget(self._time_current)
        time_layout.addStretch()
        time_layout.addWidget(self._time_total)
        layout.addLayout(time_layout)

        # ── Кнопки управления ──
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)

        self._prev_btn = QPushButton("⏮")
        self._prev_btn.setToolTip("Предыдущий (←)")
        self._prev_btn.clicked.connect(self._player.play_prev)

        self._play_btn = QPushButton("▶")
        self._play_btn.setObjectName("playBtn")
        self._play_btn.setToolTip("Играть / Пауза (Space)")
        self._play_btn.clicked.connect(self._on_play_pause)

        self._next_btn = QPushButton("⏭")
        self._next_btn.setToolTip("Следующий (→)")
        self._next_btn.clicked.connect(self._player.play_next)

        self._stop_btn = QPushButton("⏹")
        self._stop_btn.setToolTip("Стоп")
        self._stop_btn.clicked.connect(self._player.stop)

        controls_layout.addStretch()
        controls_layout.addWidget(self._prev_btn)
        controls_layout.addWidget(self._play_btn)
        controls_layout.addWidget(self._next_btn)
        controls_layout.addWidget(self._stop_btn)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # ── Громкость ──
        vol_layout = QHBoxLayout()
        vol_layout.setSpacing(6)
        vol_label = QLabel("🔊")
        vol_label.setObjectName("timeLabel")
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(50)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        vol_layout.addWidget(vol_label)
        vol_layout.addWidget(self._volume_slider, stretch=1)

        # Кнопка вставки URL
        self._url_btn = QPushButton("🔗")
        self._url_btn.setToolTip("Вставить ссылку на аудио")
        self._url_btn.clicked.connect(self._on_enter_url)
        vol_layout.addWidget(self._url_btn)

        layout.addLayout(vol_layout)

        # ── Разделитель ──
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #313244; max-height: 1px;")
        layout.addWidget(line)

        # ── QStackedWidget: плейлист / Radio Record ──
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, stretch=1)

        # Страница 0: список треков
        self._playlist_widget = QListWidget()
        self._playlist_widget.setAlternatingRowColors(False)
        self._playlist_widget.itemDoubleClicked.connect(self._on_track_selected)
        self._playlist_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._playlist_widget.customContextMenuRequested.connect(self._on_context_menu)
        self._stack.addWidget(self._playlist_widget)

        # Страница 1: Radio Record (веб-интерфейс)
        self._record_widget = QWidget()
        self._setup_record_widget()
        self._stack.addWidget(self._record_widget)

        self._stack.setCurrentIndex(0)

        # ── Статус ──
        self._status_label = QLabel(
            "💡  Откройте папку с музыкой или начните поиск"
        )
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

    def _setup_record_widget(self):
        """Создание виджета Radio Record."""
        record_layout = QVBoxLayout(self._record_widget)
        record_layout.setContentsMargins(0, 0, 0, 0)
        record_layout.setSpacing(4)

        if HAS_WEBENGINE:
            # Встроенный веб-браузер
            self._web_view = QWebEngineView()
            self._web_view.setUrl(QUrl("https://www.radiorecord.ru/"))
            self._web_view.setMinimumHeight(300)

            # Панель управления веб-вью
            web_controls = QHBoxLayout()
            web_controls.setSpacing(4)

            self._web_back_btn = QPushButton("◀")
            self._web_back_btn.setToolTip("Назад")
            self._web_back_btn.setFixedWidth(36)
            self._web_back_btn.clicked.connect(self._web_view.back)

            self._web_forward_btn = QPushButton("▶")
            self._web_forward_btn.setToolTip("Вперёд")
            self._web_forward_btn.setFixedWidth(36)
            self._web_forward_btn.clicked.connect(self._web_view.forward)

            self._web_reload_btn = QPushButton("🔄")
            self._web_reload_btn.setToolTip("Обновить")
            self._web_reload_btn.setFixedWidth(36)
            self._web_reload_btn.clicked.connect(self._web_view.reload)

            self._web_home_btn = QPushButton("🏠")
            self._web_home_btn.setToolTip("На главную radiorecord.ru")
            self._web_home_btn.setFixedWidth(36)
            self._web_home_btn.clicked.connect(
                lambda: self._web_view.setUrl(QUrl("https://www.radiorecord.ru/"))
            )

            self._web_url_label = QLabel("https://www.radiorecord.ru/")
            self._web_url_label.setObjectName("statusLabel")
            self._web_view.urlChanged.connect(
                lambda url: self._web_url_label.setText(url.toString())
            )

            web_controls.addWidget(self._web_back_btn)
            web_controls.addWidget(self._web_forward_btn)
            web_controls.addWidget(self._web_reload_btn)
            web_controls.addWidget(self._web_home_btn)
            web_controls.addWidget(self._web_url_label, stretch=1)

            record_layout.addLayout(web_controls)
            record_layout.addWidget(self._web_view, stretch=1)

            # Подсказка
            hint = QLabel(
                "💡  Авторизуйтесь на сайте для доступа к избранным каналам. "
                "Нажмите «Play» на станции для прослушивания через браузер."
            )
            hint.setObjectName("statusLabel")
            hint.setWordWrap(True)
            record_layout.addWidget(hint)
        else:
            # QtWebEngine не доступен — открываем во внешнем браузере
            no_web_label = QLabel(
                "📻  Radio Record\n\n"
                "QtWebEngine не установлен.\n"
                "Нажмите кнопку ниже, чтобы открыть сайт в браузере."
            )
            no_web_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_web_label.setWordWrap(True)

            open_browser_btn = QPushButton("🌐  Открыть Radio Record в браузере")
            open_browser_btn.setMinimumHeight(48)
            open_browser_btn.clicked.connect(self._open_record_in_browser)

            record_layout.addStretch()
            record_layout.addWidget(no_web_label)
            record_layout.addWidget(open_browser_btn)
            record_layout.addStretch()

    def _open_record_in_browser(self):
        """Открыть Radio Record во внешнем браузере."""
        import webbrowser
        webbrowser.open("https://www.radiorecord.ru/")
        self._status_label.setText("🌐  Radio Record открыт в браузере")

    def _connect_signals(self):
        """Подключение сигналов плеера."""
        self._player.track_changed.connect(self._on_track_changed)
        self._player.state_changed.connect(self._on_state_changed)
        self._player.search_results.connect(self._on_search_results)
        self._player.search_error.connect(self._on_search_error)
        self._player.error.connect(self._on_error)
        self._player.duration_changed.connect(self._on_duration_changed)
        self._player.favorites_changed.connect(self._on_favorites_changed)
        self._player.stream_metadata_changed.connect(self._on_stream_metadata)

    # ── Toggle Radio Record ──

    @Slot()
    def _on_toggle_record(self):
        """Переключение между плейлистом и Radio Record."""
        self._record_mode = self._record_btn.isChecked()

        if self._record_mode:
            self._stack.setCurrentIndex(1)
            self._status_label.setText("📻  Radio Record — выберите станцию на сайте")
            # Если QtWebEngine доступен, фокус на веб-вью
            if HAS_WEBENGINE and hasattr(self, '_web_view'):
                self._web_view.setFocus()
        else:
            self._stack.setCurrentIndex(0)
            self._status_label.setText("💡  Вернулись к плейлисту")

    # ── Прямой эфир Radio Record (без рекламы) ──

    @Slot()
    def _on_load_record_live(self):
        """Загрузить станции Radio Record через API и воспроизвести без рекламы."""
        # Если в режиме сайта — выключаем его
        if self._record_mode:
            self._record_btn.setChecked(False)
            self._on_toggle_record()

        self._status_label.setText("📡  Загрузка станций Radio Record...")
        self._playlist_widget.clear()
        self._player.load_record_stations()

    # ── Drag & Drop ──

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return

        # Если в режиме Radio Record — переключаемся на плейлист
        if self._record_mode:
            self._record_btn.setChecked(False)
            self._on_toggle_record()

        folders = set()
        files = []

        for url in urls:
            path = url.toLocalFile()
            if not path:
                # Это URL, а не локальный файл — пробуем воспроизвести
                audio_url = url.toString()
                if audio_url and self._is_audio_url(audio_url):
                    self._player.play_url(audio_url)
                    self._status_label.setText(f"🔗  Воспроизведение по ссылке: {audio_url[:50]}...")
                    return
                continue
            p = Path(path)
            if p.is_dir():
                folders.add(str(p))
            elif p.suffix.lower() in MusicPlayer.AUDIO_EXTENSIONS:
                files.append(str(p))
            elif p.suffix.lower() in {'.m3u', '.m3u8'}:
                self._player.load_playlist_file(str(p))
                return

        if folders:
            # Берём первую папку
            self._player.load_folder(list(folders)[0])
        elif files:
            tracks = []
            for f in files:
                p = Path(f)
                track = Track(
                    title=p.stem,
                    url=f.replace('\\', '/'),
                    source='local',
                    filepath=f,
                )
                tracks.append(track)
            self._player.set_playlist(tracks, 0)

    @staticmethod
    def _is_audio_url(url: str) -> bool:
        """Проверяет, является ли URL ссылкой на аудио."""
        audio_exts = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus'}
        path = url.split('?')[0].split('#')[0].lower()
        return any(path.endswith(ext) for ext in audio_exts)

    # ── Слоты ──

    @Slot()
    def _on_search(self):
        """Поиск в VK Музыке."""
        # Если в режиме Radio Record — переключаемся
        if self._record_mode:
            self._record_btn.setChecked(False)
            self._on_toggle_record()

        query = self._search_input.text().strip()
        if not query:
            return

        self._search_query = query
        self._status_label.setText(f"🔍  Поиск в VK: {query}...")
        self._playlist_widget.clear()
        self._player.search_online(query, max_results=15)

    @Slot()
    def _on_open_folder(self):
        """Открыть папку с музыкой."""
        # Если в режиме Radio Record — переключаемся
        if self._record_mode:
            self._record_btn.setChecked(False)
            self._on_toggle_record()

        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку с музыкой",
        )
        if folder:
            self._status_label.setText(f"📁  Загрузка: {Path(folder).name}...")
            tracks = self._player.load_folder(folder)
            if tracks:
                self._update_playlist_display(tracks)
                self._status_label.setText(f"📁  Загружено {len(tracks)} треков из {Path(folder).name}")
            else:
                self._status_label.setText(f"📁  В папке {Path(folder).name} нет аудиофайлов")

    @Slot()
    def _on_load_playlist(self):
        """Загрузить .m3u плейлист."""
        # Если в режиме Radio Record — переключаемся
        if self._record_mode:
            self._record_btn.setChecked(False)
            self._on_toggle_record()

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Выберите плейлист", '',
            "Плейлисты (*.m3u *.m3u8);;Все файлы (*)",
        )
        if filepath:
            self._status_label.setText(f"📋  Загрузка плейлиста...")
            tracks = self._player.load_playlist_file(filepath)
            if tracks:
                self._update_playlist_display(tracks)
                self._status_label.setText(f"📋  Загружено {len(tracks)} треков из плейлиста")
            else:
                self._status_label.setText("📋  Не найдено треков в плейлисте")

    @Slot()
    def _on_enter_url(self):
        """Вставить ссылку на аудио."""
        from PySide6.QtWidgets import QInputDialog
        url, ok = QInputDialog.getText(
            self, "Вставить ссылку",
            "Введите прямую ссылку на аудиофайл (mp3, wav и т.д.):",
        )
        if ok and url.strip():
            self._player.play_url(url.strip())
            self._status_label.setText(f"🔗  Воспроизведение по ссылке")

    @Slot()
    def _on_play_pause(self):
        self._player.toggle_play_pause()

    @Slot()
    def _on_track_selected(self, item: QListWidgetItem):
        track = item.data(Qt.ItemDataRole.UserRole)
        if track:
            self._player.play_track(track)

    @Slot(object)
    def _on_track_changed(self, track: Track):
        self._current_track = track
        source_icon = {'local': '💿', 'vk': '🌐', 'url': '🔗', 'record': '📻'}.get(track.source, '🎵')
        self._track_label.setText(f"{source_icon}  {track.display_name}")
        self._position_slider.setValue(0)
        self._time_current.setText("0:00")
        self._position_timer.start()

        # Сбрасываем метаданные радио-потока
        self._radio_meta_label.hide()
        self._copy_btn.hide()

        # Подсветить текущий трек в списке
        for i in range(self._playlist_widget.count()):
            item = self._playlist_widget.item(i)
            t = item.data(Qt.ItemDataRole.UserRole)
            if t and t.url == track.url:
                self._playlist_widget.setCurrentItem(item)
                break

    @Slot(str, str)
    def _on_stream_metadata(self, artist: str, title: str):
        """Обновить отображение метаданных радио-потока."""
        if artist and title:
            text = f"🎵  {artist} — {title}"
        elif title:
            text = f"🎵  {title}"
        else:
            return

        self._radio_meta_label.setText(text)
        self._radio_meta_label.show()
        self._copy_btn.show()
        self._status_label.setText(f"📻  {text}")

    @Slot()
    def _on_copy_track_name(self):
        """Скопировать название текущего трека из радио-потока в буфер обмена."""
        text = self._radio_meta_label.text()
        if text:
            # Убираем эмодзи в начале
            clean = text
            if clean.startswith('🎵  '):
                clean = clean[4:]
            clipboard = QApplication.clipboard()
            clipboard.setText(clean)
            self._status_label.setText(f"📋  Скопировано: {clean}")

    @Slot(str)
    def _on_state_changed(self, state: str):
        if state == 'playing':
            self._play_btn.setText("⏸")
            name = self._current_track.display_name if self._current_track else ''
            self._status_label.setText(f"▶  {name}")
        elif state == 'paused':
            self._play_btn.setText("▶")
            self._status_label.setText("⏸  Пауза")
        elif state == 'stopped':
            self._play_btn.setText("▶")
            self._track_label.setText("🎵  Нет трека")
            self._status_label.setText("⏹  Остановлено")
            self._position_timer.stop()
            self._position_slider.setValue(0)
            self._time_current.setText("0:00")

    @Slot(list)
    def _on_search_results(self, tracks: list):
        # Определяем, откуда пришли результаты — из VK или Radio Record
        if tracks and tracks[0].source == 'record':
            # Сохраняем полный список станций для фильтрации избранного
            self._all_record_tracks = tracks
            self._showing_favorites = False
            self._fav_btn.setChecked(False)
            self._update_playlist_display(tracks)
            self._status_label.setText(f"📻  Radio Record: {len(tracks)} станций загружено")
        else:
            self._update_playlist_display(tracks)
            if tracks:
                self._status_label.setText(f"🌐  VK: найдено {len(tracks)} треков")
            else:
                self._status_label.setText("😕  Ничего не найдено в VK Музыке")

    @Slot(str)
    def _on_search_error(self, msg: str):
        self._status_label.setText(f"❌  VK: {msg}")
        QMessageBox.warning(
            self, "Ошибка поиска",
            "VK Музыка недоступна. Используйте локальные файлы "
            "(📁) или вставьте ссылку вручную (🔗)."
        )

    @Slot(str)
    def _on_error(self, msg: str):
        self._status_label.setText(f"❌  {msg}")

    @Slot(int)
    def _on_duration_changed(self, duration_ms: int):
        self._position_slider.setRange(0, duration_ms)
        self._time_total.setText(self._ms_to_str(duration_ms))

    @Slot()
    def _update_position_slider(self):
        if self._player.is_playing:
            pos = self._player.position
            self._position_slider.blockSignals(True)
            self._position_slider.setValue(pos)
            self._position_slider.blockSignals(False)
            self._time_current.setText(self._ms_to_str(pos))

    @Slot(int)
    def _on_volume_changed(self, value: int):
        self._player.volume = value / 100.0

    # ── Контекстное меню ──

    def _on_context_menu(self, pos):
        item = self._playlist_widget.itemAt(pos)
        if not item:
            return

        track = item.data(Qt.ItemDataRole.UserRole)
        if not track:
            return

        menu = QMenu(self)
        play_action = QAction("▶  Воспроизвести", self)
        play_action.triggered.connect(lambda: self._player.play_track(track))
        menu.addAction(play_action)

        # Пункт избранного для станций Radio Record
        if track.source == 'record':
            is_fav = self._player.favorites.is_favorite(track.title)
            if is_fav:
                fav_action = QAction("⭐  Убрать из избранного", self)
            else:
                fav_action = QAction("☆  В избранное", self)
            fav_action.triggered.connect(
                lambda: self._toggle_favorite(track.title, track.url)
            )
            menu.addAction(fav_action)

        if track.source == 'local' and track.filepath:
            show_action = QAction("📂  Показать в проводнике", self)
            show_action.triggered.connect(lambda: self._show_in_explorer(track.filepath))
            menu.addAction(show_action)

        info_action = QAction("ℹ️  Информация", self)
        info_action.triggered.connect(lambda: self._show_track_info(track))
        menu.addAction(info_action)

        menu.exec(self._playlist_widget.viewport().mapToGlobal(pos))

    def _show_in_explorer(self, filepath: str):
        import subprocess
        subprocess.Popen(['explorer', '/select,', filepath])

    def _show_track_info(self, track: Track):
        info = (
            f"Название: {track.title or '—'}\n"
            f"Исполнитель: {track.artist or '—'}\n"
            f"Длительность: {track.duration_str}\n"
            f"Источник: {track.source}\n"
            f"Путь: {track.url}"
        )
        QMessageBox.information(self, "Информация о треке", info)

    # ── Отображение списка ──

    def _update_playlist_display(self, tracks: list[Track]):
        """Обновить отображение плейлиста."""
        self._playlist_widget.clear()
        for track in tracks:
            item = QListWidgetItem()
            text = track.display_name
            if track.duration > 0:
                text += f"  [{track.duration_str}]"

            source_icon = {'local': '💿', 'vk': '🌐', 'url': '🔗', 'record': '📻'}.get(track.source, '🎵')

            # Показываем звёздочку для избранных станций Radio Record
            fav_mark = ''
            if track.source == 'record' and self._player.favorites.is_favorite(track.title):
                fav_mark = '⭐ '

            item.setText(f"{fav_mark}{source_icon}  {text}")
            item.setData(Qt.ItemDataRole.UserRole, track)

            source_names = {'local': 'Локальный', 'vk': 'VK Музыка', 'url': 'Ссылка', 'record': 'Radio Record'}
            fav_tip = '⭐ Избранная станция\n' if track.source == 'record' and self._player.favorites.is_favorite(track.title) else ''
            item.setToolTip(
                f"{fav_tip}{track.display_name}\n"
                f"Источник: {source_names.get(track.source, track.source)}\n"
                f"Длительность: {track.duration_str}"
            )

            self._playlist_widget.addItem(item)

    # ── Утилиты ──

    @staticmethod
    def _ms_to_str(ms: int) -> str:
        if ms < 0:
            return "0:00"
        total_sec = ms // 1000
        m, s = divmod(total_sec, 60)
        return f"{m}:{s:02d}"

    # ── Избранные станции Radio Record ──

    def _toggle_favorite(self, station_name: str, stream_url: str):
        """Переключить статус избранного для станции."""
        now_fav = self._player.favorites.toggle(station_name, stream_url)
        if now_fav:
            self._status_label.setText(f"⭐  «{station_name}» добавлена в избранное")
        else:
            self._status_label.setText(f"☆  «{station_name}» удалена из избранного")
        self._player.favorites_changed.emit()

    @Slot()
    def _on_show_favorites(self):
        """Показать/скрыть избранные станции."""
        if not self._all_record_tracks:
            self._status_label.setText("⭐  Сначала загрузите станции Radio Record (📡)")
            self._fav_btn.setChecked(False)
            return

        self._showing_favorites = self._fav_btn.isChecked()

        if self._showing_favorites:
            # Показываем только избранные станции
            fav_names = self._player.favorites.get_all()
            filtered = [t for t in self._all_record_tracks if t.title in fav_names]
            if filtered:
                self._update_playlist_display(filtered)
                self._status_label.setText(f"⭐  Избранные станции: {len(filtered)}")
            else:
                self._status_label.setText("⭐  Нет избранных станций. Добавьте через контекстное меню")
                self._fav_btn.setChecked(False)
                self._showing_favorites = False
                # Показываем все станции
                self._update_playlist_display(self._all_record_tracks)
        else:
            # Показываем все станции
            self._update_playlist_display(self._all_record_tracks)
            self._status_label.setText(f"📻  Radio Record: {len(self._all_record_tracks)} станций")

    @Slot()
    def _on_favorites_changed(self):
        """Обновить отображение при изменении списка избранного."""
        # Обновляем тултип кнопки
        count = self._player.favorites.count()
        self._fav_btn.setToolTip(f"Избранные станции Radio Record ({count})")

        # Перерисовываем текущий список, чтобы обновить значки ⭐
        if self._all_record_tracks:
            if self._showing_favorites:
                self._on_show_favorites()
            else:
                # Просто перерисовываем тот же список с обновлёнными ⭐
                self._update_playlist_display(self._all_record_tracks)

    # ── Запуск ──

    def closeEvent(self, event):
        self._position_timer.stop()
        self._player.cleanup()
        super().closeEvent(event)


def run_player():
    """Запустить плеер как отдельное приложение."""
    import sys
    app = QApplication(sys.argv)
    app.setApplicationName("Music Player")

    window = MusicPlayerGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    run_player()