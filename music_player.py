"""
music_player.py — Ядро плеера для Android (Kivy).

Возможности:
  - Воспроизведение локальных аудиофайлов
  - Плейлисты
  - Radio Record (прямой эфир без рекламы, 60+ станций)
  - Вставка прямой ссылки на аудио
  - Избранные станции (сохраняются между запусками)
  - Автоматическое переподключение при обрыве потока
"""

import json
import logging
import os
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional
from threading import Thread
from time import sleep

logger = logging.getLogger(__name__)


def _get_data_dir() -> Path:
    """
    Возвращает стабильный путь для хранения данных приложения на Android.
    """
    android_data = os.environ.get('ANDROID_APP_DATA_DIR') or os.environ.get('EXTERNAL_STORAGE')
    if android_data:
        return Path(android_data) / 'RadioPlayer'
    try:
        home = Path.home()
        if home:
            return home / '.RadioPlayer'
    except Exception:
        pass
    return Path(__file__).parent


DATA_DIR = _get_data_dir()
FAVORITES_FILE = DATA_DIR / 'favorites.json'


# ──────────────────────────────────────────────
# Модель данных трека
# ──────────────────────────────────────────────

class Track:
    """Информация о треке."""

    __slots__ = ('title', 'artist', 'duration', 'url', 'thumbnail', 'source', 'filepath')

    def __init__(
        self,
        title: str = '',
        artist: str = '',
        duration: int = 0,
        url: str = '',
        thumbnail: str = '',
        source: str = 'local',
        filepath: str = '',
    ):
        self.title = title
        self.artist = artist
        self.duration = duration
        self.url = url
        self.thumbnail = thumbnail
        self.source = source
        self.filepath = filepath

    @property
    def display_name(self) -> str:
        if self.artist:
            return f"{self.artist} — {self.title}"
        return self.title or Path(self.url).stem if self.url else 'Unknown'

    @property
    def duration_str(self) -> str:
        m, s = divmod(self.duration, 60)
        if m >= 60:
            h, m = divmod(m, 60)
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    def __repr__(self) -> str:
        return f"Track({self.display_name!r}, {self.duration_str})"


# ──────────────────────────────────────────────
# Менеджер избранных станций Radio Record
# ──────────────────────────────────────────────

class FavoritesManager:
    """Управление списком избранных радиостанций.

    Хранит избранное в JSON-файле favorites.json в каталоге данных приложения.
    Формат: {station_name: stream_url}
    """

    def __init__(self, filepath: Optional[Path] = None):
        self._filepath = filepath or FAVORITES_FILE
        self._favorites: dict[str, str] = {}
        self._load()

    def _load(self):
        """Загрузить избранное из JSON-файла."""
        try:
            if self._filepath.exists():
                with open(self._filepath, 'r', encoding='utf-8') as f:
                    self._favorites = json.load(f)
            else:
                self._favorites = {}
        except Exception as e:
            logger.warning(f"Не удалось загрузить избранное: {e}")
            self._favorites = {}

    def save(self):
        """Сохранить избранное в JSON-файл."""
        try:
            self._filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self._filepath, 'w', encoding='utf-8') as f:
                json.dump(self._favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Не удалось сохранить избранное: {e}")

    def add(self, name: str, stream_url: str) -> bool:
        if name not in self._favorites:
            self._favorites[name] = stream_url
            self.save()
            return True
        return False

    def remove(self, name: str) -> bool:
        if name in self._favorites:
            del self._favorites[name]
            self.save()
            return True
        return False

    def toggle(self, name: str, stream_url: str) -> bool:
        if name in self._favorites:
            self.remove(name)
            return False
        else:
            self.add(name, stream_url)
            return True

    def is_favorite(self, name: str) -> bool:
        return name in self._favorites

    def get_all(self) -> dict[str, str]:
        return dict(self._favorites)

    def count(self) -> int:
        return len(self._favorites)


# ──────────────────────────────────────────────
# Radio Record: станции
# ──────────────────────────────────────────────

RECORD_STATIONS_FALLBACK = {
    'Record':            ('rr_main', 'Main — танцевальная музыка'),
    'Deep':              ('deep', 'Deep — глубокая хаус-музыка'),
    'Pumpkin':           ('pumpkin', 'Pumpkin — дабстеп / даб'),
    'Dubstep':           ('dubstep', 'Dubstep — дабстеп'),
    'Trancehouse':       ('trancehouse', 'Trancehouse — транс-хаус'),
    'Techno':            ('techno', 'Techno — техно'),
    'Breaks':            ('breaks', 'Breaks — брейкбит'),
    'House':             ('house', 'House — хаус'),
    'Club':              ('club', 'Club — клубная музыка'),
    'VIP':               ('vip', 'VIP — танцевальные хиты'),
    'Russian':           ('russian', 'Russian — русские хиты'),
    'Rock':              ('rock', 'Rock — рок'),
    'Rap':               ('rap', 'Rap — рэп / хип-хоп'),
    'Pop':               ('pop', 'Pop — поп-музыка'),
    'Chill':             ('chill', 'Chill — чиллаут / лаунж'),
    'Jazz':              ('jazz', 'Jazz — джаз'),
    'Classic':           ('classic', 'Classic — классика'),
    'Gold':              ('gold', 'Gold — золотые хиты'),
    'Disco':             ('disco', 'Disco — диско'),
    'Eurodance':         ('eurodance', 'Eurodance — евродэнс'),
    'Trance':            ('trance', 'Trance — транс'),
    'Drum&Bass':         ('dnb', 'Drum & Bass — драм-н-бейс'),
    'Hardstyle':         ('hardstyle', 'Hardstyle — хардстайл'),
    'Hardbass':          ('hardbass', 'Hardbass — хардбасс'),
    'Basshouse':         ('basshouse', 'Bass House — басс-хаус'),
    'Minimal':           ('minimal', 'Minimal — минимал-техно'),
    'Progressive':       ('progressive', 'Progressive — прогрессив'),
    'Ambient':           ('ambient', 'Ambient — эмбиент'),
    'Lounge':            ('lounge', 'Lounge — лаунж'),
    'Soul':              ('soul', 'Soul — соул'),
    'Funk':              ('funk', 'Funk — фанк'),
    'Reggae':            ('reggae', 'Reggae — регги'),
    'Trap':              ('trap', 'Trap — трэп'),
    'EDM':               ('edm', 'EDM — электронная танцевальная музыка'),
    'Synthwave':         ('synthwave', 'Synthwave — синтвейв'),
    'Podcast':           ('podcast', 'Podcast — подкасты Record'),
    'Neurofunk':         ('neurofunk', 'Neurofunk — нейрофанк'),
    'Liquid':            ('liquid', 'Liquid — ликвид драм-н-бейс'),
    'Jungle':            ('jungle', 'Jungle — джангл'),
    'Midtempo':          ('midtempo', 'Midtempo — мидтемпо'),
    'Riddim':            ('riddim', 'Riddim — риддим'),
    'Tearout':           ('tearout', 'Tearout — тераут'),
    'Wave':              ('wave', 'Wave — вейв'),
    'Gothic':            ('gothic', 'Gothic — готика'),
    'Industrial':        ('industrial', 'Industrial — индастриал'),
    'Metal':             ('metal', 'Metal — метал'),
    'Punk':              ('punk', 'Punk — панк'),
    'Ska':               ('ska', 'Ska — ска'),
    'Alternative':       ('alternative', 'Alternative — альтернатива'),
    'Indie':             ('indie', 'Indie — инди'),
    'Folk':              ('folk', 'Folk — фолк'),
    'Country':           ('country', 'Country — кантри'),
    'Blues':             ('blues', 'Blues — блюз'),
    'RnB':               ('rnb', 'R&B — ритм-н-блюз'),
    'Latino':            ('latino', 'Latino — латино'),
    'Kpop':              ('kpop', 'K-Pop — кей-поп'),
    'Dance':             ('dance', 'Dance — танцевальная музыка'),
    'Super':             ('super', 'Super — супер-хиты'),
    'Megamix':           ('megamix', 'Megamix — мегамикс'),
    'Fresh':             ('fresh', 'Fresh — свежие треки'),
    'Chart':             ('chart', 'Chart — чарты'),
    'Hits':              ('hits', 'Hits — хиты'),
    'Workout':           ('workout', 'Workout — для тренировок'),
    'Drive':             ('drive', 'Drive — драйв'),
    'Night':             ('night', 'Night — ночная музыка'),
    'Morning':           ('morning', 'Morning — утренняя музыка'),
    'Relax':             ('relax', 'Relax — расслабляющая музыка'),
    'Party':             ('party', 'Party — вечеринка'),
    'Mayak':             ('mayak', 'Mayak — маяк'),
    'Utopia':            ('utopia', 'Utopia — утопия'),
    'RusZima':           ('ruszima', 'Русская Зима — зимние хиты'),
    'Christmas':         ('christmas', 'Christmas — рождественские хиты'),
    'ChristmasChill':    ('christmaschill', 'Christmas Chill — рождественский чилл'),
}


def load_record_stations() -> dict:
    """
    Загрузить станции Radio Record.
    Сначала пробует API, при ошибке — fallback.
    """
    try:
        req = urllib.request.Request(
            'https://radiorecord.ru/api/stations/',
            headers={'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36'},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        stations = {}
        if 'result' in data and 'stations' in data['result']:
            for s in data['result']['stations']:
                title = s.get('title', '')
                tooltip = s.get('tooltip', '')
                stream_url = s.get('stream_128', '') or s.get('stream_64', '')
                if title and stream_url:
                    display_name = f"{title} — {tooltip}" if tooltip else title
                    stations[display_name] = stream_url

        if stations:
            has_main = any('Record' in k for k in stations)
            if not has_main:
                stations['Record — Главная'] = 'https://radiorecord.hostingradio.ru/rr_main96.aacp'
            return stations
    except Exception as e:
        logger.warning(f"Record API недоступен: {e}")

    # Fallback
    stations = {}
    for name, (prefix, desc) in RECORD_STATIONS_FALLBACK.items():
        stations[f"{name} — {desc}"] = f'https://radiorecord.hostingradio.ru/{prefix}96.aacp'
    return stations


# ──────────────────────────────────────────────
# Основной плеер (синхронная версия для Kivy)
# ──────────────────────────────────────────────

class MusicPlayer:
    """
    Аудио-плеер для Android (Kivy).
    Воспроизведение через SoundLoader.
    """

    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus'}

    def __init__(self):
        self._current_track: Optional[Track] = None
        self._playlist: list[Track] = []
        self._playlist_index: int = -1
        self._volume: float = 0.5
        self._sound = None
        self._is_playing = False

        # Менеджер избранных станций
        self.favorites = FavoritesManager()

        # Параметры переподключения для радио-потоков
        self._is_stream: bool = False
        self._reconnect_thread: Optional[Thread] = None
        self._reconnect_attempts: int = 0
        self._max_reconnect_attempts: int = 5
        self._should_reconnect: bool = False

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(0.0, min(1.0, value))
        if self._sound:
            try:
                self._sound.volume = self._volume
            except Exception:
                pass

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    @property
    def current_track(self) -> Optional[Track]:
        return self._current_track

    @property
    def playlist(self) -> list[Track]:
        return list(self._playlist)

    @property
    def playlist_index(self) -> int:
        return self._playlist_index

    def play(self):
        if self._sound:
            try:
                self._sound.play()
                self._is_playing = True
            except Exception as e:
                logger.error(f"play error: {e}")

    def pause(self):
        if self._sound:
            try:
                self._sound.stop()
                self._is_playing = False
            except Exception as e:
                logger.error(f"pause error: {e}")

    def stop(self):
        self._should_reconnect = False
        self._reconnect_attempts = 0
        if self._sound:
            try:
                self._sound.stop()
                self._sound.unload()
            except Exception:
                pass
            self._sound = None
        self._is_playing = False
        self._current_track = None

    def toggle_play_pause(self):
        if self._is_playing:
            self.pause()
        else:
            self.play()

    def set_playlist(self, tracks: list[Track], start_index: int = 0):
        self._playlist = list(tracks)
        self._playlist_index = start_index
        if self._playlist:
            self._play_track_at(start_index)

    def add_to_playlist(self, track: Track):
        self._playlist.append(track)

    def play_next(self):
        if self._playlist and self._playlist_index < len(self._playlist) - 1:
            self._play_track_at(self._playlist_index + 1)

    def play_prev(self):
        if self._playlist and self._playlist_index > 0:
            self._play_track_at(self._playlist_index - 1)

    def _play_track_at(self, index: int):
        if 0 <= index < len(self._playlist):
            self._playlist_index = index
            self.play_track(self._playlist[index])

    def play_track(self, track: Track):
        """Воспроизвести трек через SoundLoader."""
        self.stop()
        self._current_track = track

        # Определяем, является ли это потоком (радио)
        self._is_stream = track.source in ('record', 'url')
        self._reconnect_attempts = 0
        self._should_reconnect = self._is_stream

        from kivy.core.audio import SoundLoader

        try:
            self._sound = SoundLoader.load(track.url)
            if self._sound:
                self._sound.volume = self._volume
                self._sound.bind(on_stop=self._on_sound_stop)
                self._sound.play()
                self._is_playing = True
            else:
                logger.error(f"SoundLoader.load() вернул None для: {track.url}")
                # Пробуем альтернативный подход для потокового аудио
                if self._is_stream:
                    self._start_reconnect()
        except Exception as e:
            logger.error(f"play_track error: {e}")
            raise

    def _on_sound_stop(self, instance):
        """Обработчик остановки звука."""
        self._is_playing = False

        if self._should_reconnect and self._is_stream and self._current_track:
            self._start_reconnect()
        else:
            self.play_next()

    def _start_reconnect(self):
        """Запустить попытку переподключения в фоновом потоке."""
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
        self._reconnect_thread = Thread(target=self._reconnect_loop, daemon=True)
        self._reconnect_thread.start()

    def _reconnect_loop(self):
        """Цикл переподключения с увеличивающимся интервалом."""
        while self._should_reconnect and self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            interval = min(self._reconnect_attempts * 5, 30)
            sleep(interval)

            if not self._should_reconnect or not self._current_track:
                return

            from kivy.core.audio import SoundLoader
            try:
                new_sound = SoundLoader.load(self._current_track.url)
                if new_sound:
                    if self._sound:
                        try:
                            self._sound.unload()
                        except Exception:
                            pass
                    self._sound = new_sound
                    self._sound.volume = self._volume
                    self._sound.bind(on_stop=self._on_sound_stop)
                    self._sound.play()
                    self._is_playing = True
                    return
            except Exception as e:
                logger.warning(f"Reconnect attempt {self._reconnect_attempts} failed: {e}")

        if self._reconnect_attempts >= self._max_reconnect_attempts:
            self._should_reconnect = False

    def load_folder(self, folder_path: str) -> list[Track]:
        path = Path(folder_path)
        if not path.is_dir():
            return []
        tracks = []
        for ext in self.AUDIO_EXTENSIONS:
            for f in sorted(path.glob(f'*{ext}')):
                track = Track(title=f.stem, url=str(f), source='local', filepath=str(f))
                tracks.append(track)
        if tracks:
            self.set_playlist(tracks, 0)
        return tracks

    def play_url(self, url: str):
        track = Track(title=url.split('/')[-1][:50], url=url, source='url')
        self.play_track(track)

    def play_record_station(self, name: str, stream_url: str):
        track = Track(title=name, url=stream_url, source='record')
        self.play_track(track)

    def get_record_stations(self) -> list[Track]:
        stations = load_record_stations()
        tracks = []
        for name, stream_url in stations.items():
            track = Track(title=name, url=stream_url, source='record')
            tracks.append(track)
        return tracks

    def cleanup(self):
        self.stop()