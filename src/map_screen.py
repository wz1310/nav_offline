"""
Layar utama — input koordinat, hitung rute, tampilkan hasil.
Peta ditampilkan via WebView (file HTML lokal dengan Leaflet + tile cache).
"""

import os
import webbrowser

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.widget import Widget
from kivy.utils import platform

from src.routing import load_graph, find_route, DATA_DIR

MAP_HTML = os.path.join(DATA_DIR, "route_map.html")

_graph = None  # graph di-load sekali saat layar dibuka

class MapPreview(Widget):
    """Widget sederhana untuk menggambar preview jaringan jalan."""
    def draw_graph(self, G):
        self.canvas.clear()
        if G is None or G.number_of_nodes() == 0:
            return

        # Ambil bounding box
        lats = [data.get('y', data.get('lat')) for n, data in G.nodes(data=True)]
        lons = [data.get('x', data.get('lon')) for n, data in G.nodes(data=True)]
        
        if not lats or not lons: return
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        def to_screen(lat, lon):
            # Normalisasi ke [0, 1] lalu ke ukuran widget
            w, h = self.size
            px, py = self.pos
            x = (lon - min_lon) / (max_lon - min_lon) * w + px
            y = (lat - min_lat) / (max_lat - min_lat) * h + py
            return x, y

        with self.canvas:
            Color(0.2, 0.3, 0.4, 0.5)
            
            # Ambil sampling edge agar tidak lag (maks 10.000 garis)
            edges = list(G.edges(data=True))
            if len(edges) > 10000:
                # Prioritaskan jalan utama jika ada atribut 'type'
                main_roads = [e for e in edges if e[2].get('type') in ['motorway', 'trunk', 'primary', 'secondary']]
                if len(main_roads) > 500:
                    edges = main_roads[:10000]
                else:
                    step = len(edges) // 10000
                    edges = edges[::step]
            
            for u, v, data in edges:
                u_data, v_data = G.nodes[u], G.nodes[v]
                u_lat = u_data.get('y', u_data.get('lat'))
                u_lon = u_data.get('x', u_data.get('lon'))
                v_lat = v_data.get('y', v_data.get('lat'))
                v_lon = v_data.get('x', v_data.get('lon'))
                
                if None not in [u_lat, u_lon, v_lat, v_lon]:
                    Line(points=[*to_screen(u_lat, u_lon), *to_screen(v_lat, v_lon)], width=1)



class MapScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def on_enter(self):
        """Dipanggil setiap kali layar ini ditampilkan."""
        global _graph
        if _graph is None:
            self._set_status("⏳ Memuat data peta…")
            import threading
            threading.Thread(target=self._load_graph_bg, daemon=True).start()

    def _load_graph_bg(self):
        global _graph
        _graph = load_graph()
        if _graph is None:
            Clock.schedule_once(lambda dt: self._set_status(
                "❌ Data belum ada. Kembali ke layar unduh."
            ))
        else:
            node_count = _graph.number_of_nodes()
            Clock.schedule_once(lambda dt: self._on_graph_loaded(_graph, node_count))

    def _on_graph_loaded(self, G, node_count):
        self._set_status(f"✅ Peta siap — {node_count:,} titik jalan dimuat.")
        self.btn_map.opacity = 1
        self.btn_map.disabled = False
        self.preview.draw_graph(G)

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=16, spacing=10)

        with root.canvas.before:
            Color(0.06, 0.07, 0.09, 1)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._upd_bg, size=self._upd_bg)

        # Header
        header = BoxLayout(size_hint_y=None, height=48, spacing=8)
        btn_back = Button(
            text="←",
            size_hint_x=None, width=44,
            background_color=(0.15, 0.15, 0.20, 1),
            color=(1, 1, 1, 1),
            font_size="18sp",
        )
        btn_back.bind(on_press=lambda *a: setattr(self.manager, "current", "download"))
        header.add_widget(btn_back)
        header.add_widget(Label(
            text="[b]Navigasi Offline[/b]",
            markup=True,
            font_size="18sp",
            color=(0.31, 0.76, 0.97, 1),
        ))
        root.add_widget(header)

        # Form koordinat
        form = GridLayout(cols=2, spacing=8, size_hint_y=None, height=180)

        form.add_widget(self._lbl("📍 Lat Awal"))
        self.inp_slat = self._inp("-6.2088")
        form.add_widget(self.inp_slat)

        form.add_widget(self._lbl("📍 Lon Awal"))
        self.inp_slon = self._inp("106.8456")
        form.add_widget(self.inp_slon)

        form.add_widget(self._lbl("🏁 Lat Tujuan"))
        self.inp_dlat = self._inp("-6.9175")
        form.add_widget(self.inp_dlat)

        form.add_widget(self._lbl("🏁 Lon Tujuan"))
        self.inp_dlon = self._inp("107.6191")
        form.add_widget(self.inp_dlon)

        root.add_widget(form)

        # Tombol hitung rute
        self.btn_route = Button(
            text="🧭  Hitung Rute",
            size_hint_y=None, height=52,
            background_color=(0.08, 0.40, 0.75, 1),
            color=(1, 1, 1, 1),
            font_size="16sp",
            bold=True,
        )
        self.btn_route.bind(on_press=self._calculate)
        root.add_widget(self.btn_route)

        # Progress
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=12)
        root.add_widget(self.progress)

        # Status
        self.status_lbl = Label(
            text="Masukkan koordinat lalu tekan Hitung Rute.",
            font_size="13sp",
            color=(0.56, 0.64, 0.68, 1),
            size_hint_y=None,
            height=52,
            halign="center",
            text_size=(360, None),
        )
        root.add_widget(self.status_lbl)

        # Tombol buka peta
        self.btn_map = Button(
            text="🌐  Buka Peta di Browser",
            size_hint_y=None, height=48,
            background_color=(0.05, 0.50, 0.35, 1),
            color=(1, 1, 1, 1),
            font_size="14sp",
            opacity=0,
            disabled=True,
        )
        self.btn_map.bind(on_press=self._open_map)
        root.add_widget(self.btn_map)

        # Area Preview Peta
        self.preview = MapPreview(size_hint_y=1)
        root.add_widget(self.preview)

        self.add_widget(root)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _upd_bg(self, inst, val):
        self._bg.pos = inst.pos
        self._bg.size = inst.size

    def _lbl(self, text):
        return Label(
            text=text, font_size="13sp",
            color=(0.56, 0.64, 0.68, 1),
            halign="right", valign="middle",
            size_hint_y=None, height=40,
        )

    def _inp(self, hint):
        return TextInput(
            text=hint,
            multiline=False,
            font_size="14sp",
            background_color=(0.10, 0.13, 0.18, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.31, 0.76, 0.97, 1),
            size_hint_y=None, height=40,
        )

    def _set_status(self, msg, pct=None):
        self.status_lbl.text = msg
        if pct is not None:
            self.progress.value = int(pct * 100)

    # ── routing ──────────────────────────────────────────────────────────────

    def _calculate(self, *args):
        try:
            olat = float(self.inp_slat.text.strip())
            olon = float(self.inp_slon.text.strip())
            dlat = float(self.inp_dlat.text.strip())
            dlon = float(self.inp_dlon.text.strip())
        except ValueError:
            self._set_status("❌ Koordinat tidak valid. Gunakan angka desimal.")
            return

        self.btn_route.disabled = True
        self.btn_map.opacity = 0
        self.btn_map.disabled = True
        self._set_status("⏳ Menghitung rute…", 0.3)

        import threading
        threading.Thread(
            target=self._route_task,
            args=(olat, olon, dlat, dlon),
            daemon=True,
        ).start()

    def _route_task(self, olat, olon, dlat, dlon):
        global _graph

        if _graph is None:
            Clock.schedule_once(lambda dt: self._finish_error(
                "Data peta belum dimuat. Tunggu sebentar atau unduh dulu."
            ))
            return

        result = find_route(_graph, olat, olon, dlat, dlon)

        if result["error"]:
            Clock.schedule_once(lambda dt: self._finish_error(result["error"]))
            return

        # Buat HTML peta
        try:
            self._build_map_html(result["coords"], olat, olon, dlat, dlon,
                                 result["distance_km"])
        except Exception as e:
            Clock.schedule_once(lambda dt: self._finish_error(
                f"Gagal membuat peta: {e}"
            ))
            return

        km = result["distance_km"]
        seg = result["segments"]
        Clock.schedule_once(lambda dt: self._finish_ok(
            f"✅ Rute ditemukan!  {km} km  |  {seg} titik jalan"
        ))

    def _finish_ok(self, msg):
        self._set_status(msg, 1.0)
        self.btn_route.disabled = False
        self.btn_map.opacity = 1
        self.btn_map.disabled = False

    def _finish_error(self, msg):
        self._set_status(f"❌ {msg}")
        self.btn_route.disabled = False

    def _open_map(self, *args):
        path = "file:///" + MAP_HTML.replace("\\", "/")
        webbrowser.open(path)

    # ── HTML builder ─────────────────────────────────────────────────────────

    def _build_map_html(self, coords, olat, olon, dlat, dlon, km):
        """Buat file HTML dengan Leaflet.js — tile dari cache lokal jika ada."""
        if not coords:
            raise ValueError("Koordinat rute kosong.")

        coords_js = str([[c[0], c[1]] for c in coords])
        center_lat = (coords[0][0] + coords[-1][0]) / 2
        center_lon = (coords[0][1] + coords[-1][1]) / 2

        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Rute Navigasi</title>
  <link rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body {{ margin:0; padding:0; background:#0f1117; }}
    #map {{ width:100vw; height:100vh; }}
    #info {{
      position:absolute; bottom:16px; left:50%; transform:translateX(-50%);
      background:rgba(15,17,23,0.88); color:#4FC3F7;
      padding:10px 20px; border-radius:20px;
      font-family:sans-serif; font-size:14px; z-index:1000;
      white-space:nowrap;
    }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="info">📍 Jarak: <b>{km} km</b></div>
  <script>
    var map = L.map('map').setView([{center_lat}, {center_lon}], 12);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    }}).addTo(map);

    var coords = {coords_js};
    var line = L.polyline(coords, {{color:'#FF4444', weight:5, opacity:0.85}}).addTo(map);
    map.fitBounds(line.getBounds(), {{padding:[20,20]}});

    L.marker([{coords[0][0]}, {coords[0][1]}])
      .bindPopup('<b>Start</b><br>{olat:.5f}, {olon:.5f}')
      .addTo(map).openPopup();
    L.marker([{coords[-1][0]}, {coords[-1][1]}])
      .bindPopup('<b>Tujuan</b><br>{dlat:.5f}, {dlon:.5f}')
      .addTo(map);
  </script>
</body>
</html>"""

        os.makedirs(os.path.dirname(MAP_HTML), exist_ok=True)
        with open(MAP_HTML, "w", encoding="utf-8") as f:
            f.write(html)
