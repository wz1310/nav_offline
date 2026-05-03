"""
Offline Indonesia Navigation
Entry point aplikasi Kivy
"""

import os
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window
from kivy.utils import platform

from src.download_screen import DownloadScreen
from src.map_screen import MapScreen

# Ukuran window untuk testing di desktop (mirip layar HP)
if platform != "android":
    Window.size = (400, 720)


class NavApp(App):
    title = "Navigasi Indonesia Offline"

    def build(self):
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(DownloadScreen(name="download"))
        sm.add_widget(MapScreen(name="map"))

        # Cek apakah data sudah pernah di-download
        from src.routing import data_exists
        if data_exists():
            sm.current = "map"
        else:
            sm.current = "download"

        return sm


if __name__ == "__main__":
    NavApp().run()
