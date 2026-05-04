"""
Offline Indonesia Navigation
Entry point aplikasi Kivy dengan pelacak error untuk debugging di HP.
"""

import os
import sys
import traceback

# Pastikan environment config bersih
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

def show_error_screen(error_msg):
    """Tampilkan error di layar jika aplikasi gagal start."""
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.core.window import Window
    
    class ErrorApp(App):
        def build(self):
            Window.clearcolor = (0.1, 0, 0, 1)  # Background merah gelap
            return Label(
                text=f"APLIKASI CRASH SAAT START:\n\n{error_msg}",
                font_size="12sp",
                halign="left",
                valign="top",
                text_size=(Window.width - 40, None),
                padding=(20, 20)
            )
    ErrorApp().run()

try:
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager, SlideTransition
    from kivy.core.window import Window
    from kivy.utils import platform

    from src.download_screen import DownloadScreen
    from src.map_screen import MapScreen

    # Ukuran window untuk testing di desktop
    if platform != "android":
        Window.size = (400, 720)

    class NavApp(App):
        title = "Navigasi Indonesia Offline"

        def build(self):
            try:
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
            except Exception as e:
                return Label(text=f"Error in build():\n{traceback.format_exc()}")

    if __name__ == "__main__":
        try:
            NavApp().run()
        except Exception as e:
            show_error_screen(traceback.format_exc())

except Exception:
    # Jika impor awal gagal, coba tampilkan error menggunakan Kivy minimal
    error_info = traceback.format_exc()
    try:
        show_error_screen(error_info)
    except:
        # Jika Kivy sendiri gagal total, tidak banyak yang bisa dilakukan di HP
        # tapi setidaknya kita mencoba.
        print(error_info)
        sys.exit(1)
