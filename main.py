"""
Navigasi Indonesia Pro Launcher
Sistem Hybrid: Python (Backend) + MapLibre GL (Frontend)
"""

import os
import webbrowser
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window

class MainApp(App):
    def build(self):
        self.title = "Navigasi Indonesia Pro"
        Window.clearcolor = (0.06, 0.07, 0.09, 1)
        
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        
        # Logo / Title
        layout.add_widget(Label(
            text="[b]NAVIGASI INDONESIA PRO[/b]",
            markup=True,
            font_size='24sp',
            color=(0.31, 0.76, 0.97, 1),
            size_hint_y=None, height=100
        ))
        
        layout.add_widget(Label(
            text="Engine Peta Pro (MapLibre GL) siap digunakan.\nTekan tombol di bawah untuk membuka navigasi.",
            halign='center',
            color=(0.7, 0.7, 0.7, 1)
        ))
        
        # Tombol Buka Peta
        btn_start = Button(
            text="🚀 BUKA NAVIGASI SEKARANG",
            size_hint_y=None, height=60,
            background_color=(0.08, 0.45, 0.8, 1),
            bold=True
        )
        btn_start.bind(on_press=self.launch_map)
        layout.add_widget(btn_start)
        
        layout.add_widget(Label(size_hint_y=1)) # Spacer
        
        return layout

    def launch_map(self, *args):
        # Path ke file HTML lokal
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "index.html"))
        url = "file://" + html_path.replace("\\", "/")
        
        print(f"Launching map at: {url}")
        webbrowser.open(url)

if __name__ == "__main__":
    MainApp().run()
