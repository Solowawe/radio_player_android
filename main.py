"""
main.py — Android-приложение радио-плеера (Kivy + KivyMD).

Возможности:
  - Radio Record: 60+ станций без рекламы
  - Избранные станции (сохраняются между запусками)
  - Автоматическое переподключение при обрыве потока
  - Локальные аудиофайлы
  - Воспроизведение по прямой ссылке
  - Материальный дизайн (KivyMD)
"""

import os
import sys
import traceback
from pathlib import Path

# ──────────────────────────────────────────────
# Глобальный перехватчик ошибок (пишет в файл на телефоне)
# ──────────────────────────────────────────────
CRASH_LOG = '/sdcard/radio_player_crash.log'

def _write_crash_log(exc_type, exc_value, exc_tb):
    """Записать traceback в файл на SD-карте."""
    try:
        with open(CRASH_LOG, 'w') as f:
            f.write(f'Type: {exc_type.__name__}\n')
            f.write(f'Value: {exc_value}\n')
            f.write('Traceback:\n')
            traceback.print_tb(exc_tb, file=f)
            f.write('\n--- sys.path ---\n')
            for p in sys.path:
                f.write(f'  {p}\n')
            f.write('--- END ---\n')
    except Exception:
        pass  # не можем даже записать лог — ничего не поделать
    # Всё равно вызываем стандартный обработчик
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _write_crash_log

from kivy.config import Config

# Настройки окна (для десктоп-тестирования; на Android игнорируются)
Config.set('graphics', 'width', '420')
Config.set('graphics', 'height', '700')
Config.set('graphics', 'resizable', False)
Config.set('kivy', 'window_icon', '')

from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.utils import platform
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.lang import Builder

from kivymd.app import MDApp
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget, TwoLineListItem, ThreeLineListItem
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.slider import MDSlider
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.textfield import MDTextField
from kivymd import fonts

from music_player import MusicPlayer, Track

from kivymd.uix.floatlayout import MDFloatLayout


class RecordTab(MDFloatLayout, MDTabsBase):
    """Вкладка Radio Record."""
    pass


class LocalTab(MDFloatLayout, MDTabsBase):
    """Вкладка локальных файлов."""
    pass


class UrlTab(MDFloatLayout, MDTabsBase):
    """Вкладка воспроизведения по ссылке."""
    pass


# ──────────────────────────────────────────────
# KV-разметка (встроенная)
# ──────────────────────────────────────────────

KV = '''
<RecordTab>:
    BoxLayout:
        orientation: 'vertical'

        MDRaisedButton:
            id: fav_filter_btn
            text: '⭐  Показать избранное'
            size_hint_y: None
            height: '40dp'
            on_release: app.toggle_favorites_filter()

        ScrollView:
            BoxLayout:
                id: stations_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height

<LocalTab>:
    BoxLayout:
        orientation: 'vertical'
        spacing: '4dp'

        MDRaisedButton:
            text: '📁  Выбрать папку'
            on_release: app.choose_folder()

        ScrollView:
            BoxLayout:
                id: local_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height

<UrlTab>:
    BoxLayout:
        orientation: 'vertical'
        spacing: '8dp'
        padding: '16dp'

        MDTextField:
            id: url_input
            hint_text: 'Введите прямую ссылку на аудио...'
            mode: 'rectangle'

        MDRaisedButton:
            text: '▶  Воспроизвести'
            on_release: app.play_url()

<MainScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: '4dp'
        padding: '4dp'

        MDTopAppBar:
            title: 'Radio Player'
            md_bg_color: app.theme_cls.primary_color
            specific_text_color: 1, 1, 1, 1
            left_action_items: [['star', lambda x: app.toggle_favorites_filter()]]
            right_action_items: [['dots-vertical', lambda x: app.open_menu()]]

        # Информация о текущем треке
        MDLabel:
            id: track_label
            text: '🎵  Нет трека'
            halign: 'center'
            font_style: 'H6'
            size_hint_y: None
            height: '48dp'

        # Ползунок позиции (условный)
        MDProgressBar:
            id: progress_bar
            value: 0
            max: 100
            size_hint_y: None
            height: '4dp'

        # Кнопки управления
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '64dp'
            spacing: '8dp'
            padding: ['16dp', '0dp', '16dp', '0dp']

            MDIconButton:
                icon: 'skip-previous'
                on_release: app.player.play_prev()

            Widget:

            MDIconButton:
                id: play_btn
                icon: 'play'
                theme_icon_size: 'Custom'
                icon_size: '48dp'
                on_release: app.toggle_play_pause()

            Widget:

            MDIconButton:
                icon: 'skip-next'
                on_release: app.player.play_next()

        # Громкость
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: '48dp'
            spacing: '8dp'
            padding: ['16dp', '0dp', '16dp', '0dp']

            MDIconButton:
                icon: 'volume-high'
                on_release: app.show_volume_dialog()

            MDSlider:
                id: volume_slider
                min: 0
                max: 100
                value: 50
                on_value: app.set_volume(self.value)

        # Вкладки: Станции / Локальные / Ссылка
        MDTabs:
            id: tabs
            on_tab_switch: app.on_tab_switch(*args)

        # Статус
        MDLabel:
            id: status_label
            text: '💡  Выберите станцию или откройте папку'
            halign: 'center'
            font_style: 'Caption'
            size_hint_y: None
            height: '32dp'
            theme_text_color: 'Hint'
'''


# ──────────────────────────────────────────────
# Экраны
# ──────────────────────────────────────────────

class MainScreen(Screen):
    pass


# ──────────────────────────────────────────────
# Кастомный элемент списка станций с поддержкой избранного
# ──────────────────────────────────────────────

class StationListItem(OneLineAvatarIconListItem):
    """Элемент списка станций Radio Record с поддержкой избранного."""

    def __init__(self, track: Track, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.track = track
        self.app_ref = app_ref
        self.text = track.title
        self.secondary_text = '📻  Radio Record'

        # Иконка избранного справа
        self.fav_icon = IconRightWidget(
            icon='star-outline',
            on_release=lambda x: self._toggle_fav(),
        )
        self.add_widget(self.fav_icon)
        self._update_fav_icon()

        # Воспроизведение по нажатию на элемент
        self.on_release = lambda: self.app_ref.play_track(self.track)

    def _toggle_fav(self):
        """Переключить избранное."""
        self.app_ref._toggle_favorite(self.track)
        self._update_fav_icon()

    def _update_fav_icon(self):
        """Обновить иконку избранного."""
        is_fav = self.app_ref.player.favorites.is_favorite(self.track.title)
        self.fav_icon.icon = 'star' if is_fav else 'star-outline'


# ──────────────────────────────────────────────
# Приложение
# ──────────────────────────────────────────────

class RadioPlayerApp(MDApp):
    """Android-приложение радио-плеера."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = MusicPlayer()
        self._stations_loaded = False
        self._all_stations: list[Track] = []
        self._showing_favorites_only = False
        self.record_tab = None
        self.local_tab = None
        self.url_tab = None

    def build(self):
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_hue = '700'

        try:
            Builder.load_string(KV)
        except Exception as e:
            # Если KV-разметка не загрузилась — показываем экран с ошибкой
            return self._build_error_screen(f"KV Error: {e}")

        self.screen = MainScreen(name='main')
        self.sm = ScreenManager()
        self.sm.add_widget(self.screen)

        # Загружаем станции при старте (с задержкой, чтобы GUI успел отрисоваться)
        Clock.schedule_once(lambda dt: self.load_stations(), 0.5)

        return self.sm

    def on_start(self):
        """Создаём вкладки программно (KivyMD 1.1.1 требует add_widget в on_start)."""
        tabs = self.screen.ids.tabs

        self.record_tab = RecordTab(title='📻 Radio Record', icon='radio')
        tabs.add_widget(self.record_tab)

        self.local_tab = LocalTab(title='💿 Локальные', icon='folder-music')
        tabs.add_widget(self.local_tab)

        self.url_tab = UrlTab(title='🔗 Ссылка', icon='link')
        tabs.add_widget(self.url_tab)

    def _build_error_screen(self, error_text: str):
        """Создать экран с ошибкой, если приложение не может запуститься."""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.textinput import TextInput
        from kivy.uix.scrollview import ScrollView

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        title = Label(
            text='[b]Radio Player — Ошибка запуска[/b]',
            markup=True,
            size_hint_y=None,
            height=60,
            color=(1, 0.3, 0.3, 1),
        )
        layout.add_widget(title)

        # Поле с текстом ошибки (прокручиваемое)
        error_input = TextInput(
            text=error_text,
            readonly=True,
            size_hint_y=0.7,
            background_color=(0.1, 0.1, 0.1, 1),
            foreground_color=(1, 0.5, 0.5, 1),
        )
        layout.add_widget(error_input)

        # Кнопка копирования ошибки
        def copy_error(btn):
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(error_text)

        copy_btn = Button(
            text='📋  Копировать ошибку',
            size_hint_y=None,
            height=50,
        )
        copy_btn.bind(on_release=copy_error)
        layout.add_widget(copy_btn)

        # Кнопка выхода
        exit_btn = Button(
            text='❌  Выйти',
            size_hint_y=None,
            height=50,
        )
        exit_btn.bind(on_release=lambda x: sys.exit(1))
        layout.add_widget(exit_btn)

        return layout

    def load_stations(self):
        """Загрузить станции Radio Record."""
        if self._stations_loaded:
            return
        self._stations_loaded = True

        print('[DEBUG] load_stations: начинаю загрузку...')
        self.show_status('📡  Загрузка станций...')
        try:
            stations = self.player.get_record_stations()
            print(f'[DEBUG] load_stations: получено {len(stations)} станций')
            self._all_stations = stations
            self._rebuild_stations_list()
            self.show_status(f'📻  Загружено {len(stations)} станций')
        except Exception as e:
            print(f'[DEBUG] load_stations: ОШИБКА {e}')
            self.show_status(f'❌  Ошибка загрузки станций: {e}')
            # Записываем в crash log
            try:
                with open(CRASH_LOG, 'a') as f:
                    f.write(f'load_stations error: {e}\n')
                    traceback.print_exc(file=f)
            except Exception:
                pass

    def _rebuild_stations_list(self):
        """Перестроить список станций с учётом фильтра избранного."""
        if not self.record_tab:
            return
        stations_list = self.record_tab.ids.stations_list
        stations_list.clear_widgets()

        tracks = self._all_stations
        if self._showing_favorites_only:
            fav_names = self.player.favorites.get_all()
            tracks = [t for t in tracks if t.title in fav_names]

        for track in tracks:
            item = StationListItem(track=track, app_ref=self)
            stations_list.add_widget(item)

        # Обновляем текст кнопки фильтра
        fav_btn = self.record_tab.ids.fav_filter_btn
        if self._showing_favorites_only:
            count = self.player.favorites.count()
            fav_btn.text = f'⭐  Избранные ({count}) — показать все'
        else:
            fav_btn.text = f'⭐  Показать избранное ({self.player.favorites.count()})'

    def toggle_favorites_filter(self):
        """Переключить фильтр «только избранные»."""
        if not self._all_stations:
            self.show_status('⭐  Сначала загрузите станции Radio Record')
            return

        self._showing_favorites_only = not self._showing_favorites_only
        self._rebuild_stations_list()

        if self._showing_favorites_only:
            count = self.player.favorites.count()
            self.show_status(f'⭐  Показано избранных: {count}')
        else:
            self.show_status(f'📻  Все станции: {len(self._all_stations)}')

    def _toggle_favorite(self, track: Track):
        """Переключить статус избранного для станции."""
        if track.source != 'record':
            return

        now_fav = self.player.favorites.toggle(track.title, track.url)
        if now_fav:
            self.show_status(f'⭐  «{track.title}» добавлена в избранное')
        else:
            self.show_status(f'☆  «{track.title}» удалена из избранного')

        # Перестраиваем список, чтобы обновить звёздочки
        self._rebuild_stations_list()

    def play_track(self, track: Track):
        """Воспроизвести трек."""
        try:
            self.player.play_track(track)
            self.screen.ids.track_label.text = f'🎵  {track.display_name}'
            self.screen.ids.play_btn.icon = 'pause'
            self.show_status(f'▶  {track.display_name}')
        except Exception as e:
            self.show_status(f'❌  Ошибка воспроизведения: {e}')
            try:
                with open(CRASH_LOG, 'a') as f:
                    f.write(f'play_track error: {e}\n')
                    traceback.print_exc(file=f)
            except Exception:
                pass

    def toggle_play_pause(self):
        """Play / Pause."""
        try:
            if self.player.is_playing:
                self.player.pause()
                self.screen.ids.play_btn.icon = 'play'
                self.show_status('⏸  Пауза')
            else:
                self.player.play()
                self.screen.ids.play_btn.icon = 'pause'
                name = self.player.current_track.display_name if self.player.current_track else ''
                self.show_status(f'▶  {name}')
        except Exception as e:
            self.show_status(f'❌  Ошибка: {e}')

    def set_volume(self, value: float):
        """Установить громкость."""
        try:
            self.player.volume = value / 100.0
        except Exception:
            pass

    def show_volume_dialog(self):
        """Показать диалог громкости."""
        pass

    def choose_folder(self):
        """Выбрать папку с музыкой."""
        if platform == 'android':
            from androidstorage4kivy import SharedStorage
            self.show_status('📁  Выберите папку через системный диалог')
        else:
            content = FileChooserListView(path=os.path.expanduser('~'))
            popup = Popup(
                title='Выберите папку с музыкой',
                content=content,
                size_hint=(0.9, 0.9),
            )
            content.on_submit = lambda selection, touch=None: self._on_folder_selected(selection, popup)
            popup.open()

    def _on_folder_selected(self, selection, popup):
        """Обработать выбор папки."""
        popup.dismiss()
        if not selection:
            return
        folder = selection[0]
        if os.path.isdir(folder):
            try:
                tracks = self.player.load_folder(folder)
                if not self.local_tab:
                    return
                local_list = self.local_tab.ids.local_list
                local_list.clear_widgets()
                for track in tracks:
                    item = TwoLineListItem(
                        text=track.title,
                        secondary_text='💿  Локальный',
                        on_release=lambda x, t=track: self.play_track(t),
                    )
                    local_list.add_widget(item)
                self.show_status(f'📁  Загружено {len(tracks)} треков')
            except Exception as e:
                self.show_status(f'❌  Ошибка загрузки: {e}')

    def play_url(self):
        """Воспроизвести по ссылке."""
        if not self.url_tab:
            return
        url = self.url_tab.ids.url_input.text.strip()
        if url:
            try:
                self.player.play_url(url)
                self.screen.ids.track_label.text = f'🔗  {url.split("/")[-1][:40]}'
                self.screen.ids.play_btn.icon = 'pause'
                self.show_status('🔗  Воспроизведение по ссылке')
            except Exception as e:
                self.show_status(f'❌  Ошибка: {e}')

    def on_tab_switch(self, *args):
        """Переключение вкладок."""
        pass

    def open_menu(self):
        """Открыть меню."""
        fav_count = self.player.favorites.count()
        dialog = MDDialog(
            title='Radio Player',
            text=(
                f'Избранных станций: {fav_count}\n\n'
                '⭐ — нажмите на звезду в тулбаре для фильтра\n'
                'Долгое нажатие на станцию — добавить/убрать из избранного\n\n'
                'Radio Record — бесплатные станции без рекламы'
            ),
            buttons=[MDFlatButton(text='OK', on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def show_status(self, text: str):
        """Показать статус."""
        try:
            self.screen.ids.status_label.text = text
        except Exception:
            pass

    def on_pause(self):
        """Обработка сворачивания приложения (Android)."""
        return True

    def on_stop(self):
        """Остановка приложения."""
        try:
            self.player.cleanup()
        except Exception:
            pass


# ──────────────────────────────────────────────
# Запуск
# ──────────────────────────────────────────────

if __name__ == '__main__':
    try:
        RadioPlayerApp().run()
    except Exception as e:
        # Если вообще не удалось запустить приложение — пишем в лог
        try:
            with open(CRASH_LOG, 'w') as f:
                f.write(f'FATAL: {e}\n')
                traceback.print_exc(file=f)
                f.write('\n--- sys.path ---\n')
                for p in sys.path:
                    f.write(f'  {p}\n')
                f.write('--- END ---\n')
        except Exception:
            pass
        raise