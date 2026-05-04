from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

import os
from src.downloader import AREA_OPTIONS, download_area, import_local_json


class DownloadScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(
            orientation="vertical",
            padding=24,
            spacing=16,
        )

        # Background gelap
        with layout.canvas.before:
            Color(0.06, 0.07, 0.09, 1)
            self._bg = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(pos=self._update_bg, size=self._update_bg)

        # Judul
        layout.add_widget(Label(
            text="[b]🗺 Navigasi Indonesia Offline[/b]",
            markup=True,
            font_size="22sp",
            color=(0.31, 0.76, 0.97, 1),
            size_hint_y=None,
            height=60,
        ))

        layout.add_widget(Label(
            text="Pilih area untuk diunduh.\nAtau impor file JSON dari HP Anda.",
            font_size="14sp",
            color=(0.56, 0.64, 0.68, 1),
            halign="center",
            size_hint_y=None,
            height=60,
        ))

        # Spinner pilih area
        self.spinner = Spinner(
            text=list(AREA_OPTIONS.keys())[0],
            values=list(AREA_OPTIONS.keys()),
            size_hint_y=None,
            height=48,
            background_color=(0.08, 0.17, 0.27, 1),
            color=(1, 1, 1, 1),
            font_size="15sp",
        )
        layout.add_widget(self.spinner)

        # Progress bar
        self.progress = ProgressBar(
            max=100, value=0,
            size_hint_y=None, height=20,
        )
        layout.add_widget(self.progress)

        # Status label
        self.status_label = Label(
            text="Siap untuk mengolah data peta.",
            font_size="13sp",
            color=(0.56, 0.64, 0.68, 1),
            size_hint_y=None,
            height=48,
            halign="center",
        )
        layout.add_widget(self.status_label)

        # Tombol unduh online
        self.btn_download = Button(
            text="⬇  Unduh Online",
            size_hint_y=None,
            height=52,
            background_color=(0.08, 0.40, 0.75, 1),
            color=(1, 1, 1, 1),
            font_size="16sp",
            bold=True,
        )
        self.btn_download.bind(on_press=self._start_download)
        layout.add_widget(self.btn_download)

        # Tombol impor lokal
        self.btn_import = Button(
            text="📁  Impor File Lokal (.json)",
            size_hint_y=None,
            height=52,
            background_color=(0.2, 0.25, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size="16sp",
        )
        self.btn_import.bind(on_press=self._show_file_picker)
        layout.add_widget(self.btn_import)

        # Tombol lanjut
        self.btn_next = Button(
            text="▶  Mulai Navigasi",
            size_hint_y=None,
            height=52,
            background_color=(0.05, 0.60, 0.40, 1),
            color=(1, 1, 1, 1),
            font_size="16sp",
            bold=True,
            opacity=0,
            disabled=True,
        )
        self.btn_next.bind(on_press=self._go_to_map)
        layout.add_widget(self.btn_next)

        layout.add_widget(Label())  # spacer
        self.add_widget(layout)

    def _update_bg(self, instance, value):
        self._bg.pos = instance.pos
        self._bg.size = instance.size

    def _show_file_picker(self, *args):
        # Gunakan FileChooser dari Plyer (Native Android Picker)
        from plyer import filechooser
        try:
            filechooser.open_file(
                title="Pilih file JSON hasil download",
                filters=[("JSON files", "*.json")],
                on_selection=self._handle_import
            )
        except Exception as e:
            self.status_label.text = f"❌ Gagal membuka picker: {str(e)}"

    def _handle_import(self, selection):
        if not selection:
            return
            
        file_path = selection[0]
        area = self.spinner.text
        
        # UI update di main thread
        def _start_proc(dt):
            self.btn_import.disabled = True
            self.btn_download.disabled = True
            self.status_label.text = f"⏳ Memproses: {os.path.basename(file_path)}"
            
            import_local_json(
                file_path=file_path,
                area_name=area,
                on_progress=self._on_progress,
                on_error=self._on_error
            )
        Clock.schedule_once(_start_proc)

    def _start_download(self, *args):
        self.btn_download.disabled = True
        self.btn_import.disabled = True
        self.btn_download.text = "⏳ Mengunduh…"
        self.progress.value = 0
        area = self.spinner.text

        download_area(
            area_name=area,
            on_progress=self._on_progress,
            on_error=self._on_error,
        )

    def _on_progress(self, message: str, pct: float):
        def _update(dt):
            self.status_label.text = message
            self.progress.value = int(pct * 100)
            if pct >= 1.0:
                self._on_done()
        Clock.schedule_once(_update)

    def _on_done(self):
        self.status_label.text = "✅ Berhasil! Data siap dipakai."
        self.progress.value = 100
        self.btn_download.text = "⬇  Unduh Lainnya"
        self.btn_download.disabled = False
        self.btn_import.disabled = False
        self.btn_next.opacity = 1
        self.btn_next.disabled = False

    def _on_error(self, message: str):
        def _update(dt):
            self.status_label.text = f"❌ {message}"
            self.btn_download.text = "⬇  Coba Lagi"
            self.btn_download.disabled = False
            self.btn_import.disabled = False
        Clock.schedule_once(_update)

    def _go_to_map(self, *args):
        self.manager.current = "map"
