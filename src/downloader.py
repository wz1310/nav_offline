"""
Download data OSM per area menggunakan Overpass API secara langsung,
lalu simpan sebagai graph pickle. Menggantikan osmnx karena masalah build di Android.
Menggunakan urllib (std lib) alih-alih requests untuk menghindari masalah arsitektur .so di Android.
"""

import threading
import urllib.request
import urllib.parse
import json
import ssl
import networkx as nx
import math
from src.routing import save_graph, DATA_DIR

# Buat context SSL yang mengabaikan verifikasi sertifikat (untuk menghindari error di Android)
ssl_context = ssl._create_unverified_context()

# Daftar area yang bisa dipilih user
AREA_OPTIONS = {
    "Jakarta & sekitarnya": "Jakarta, Indonesia",
    "Bandung & sekitarnya": "Bandung, Indonesia",
    "Surabaya & sekitarnya": "Surabaya, Indonesia",
    "Medan & sekitarnya": "Medan, Indonesia",
    "Makassar & sekitarnya": "Makassar, Indonesia",
    "Yogyakarta & sekitarnya": "Yogyakarta, Indonesia",
    "Semarang & sekitarnya": "Semarang, Indonesia",
    "Bali (Denpasar)": "Denpasar, Indonesia",
}


def haversine(lat1, lon1, lat2, lon2):
    """Hitung jarak antara dua koordinat dalam meter."""
    R = 6371000  # Radius bumi (m)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def download_area(area_name: str,
                  on_progress,
                  on_done,
                  on_error) -> None:
    """
    Download graph OSM untuk area tertentu di thread terpisah.
    """
    query_text = AREA_OPTIONS.get(area_name)
    if query_text is None:
        on_error(f"Area tidak dikenal: {area_name}")
        return

    def _task():
        try:
            # 1. Geocoding via Nominatim
            on_progress("Mencari koordinat area...", 0.1)
            # Gunakan User-Agent yang lebih spesifik dan unik
            headers = {
                'User-Agent': 'NavigasiIndonesiaOfflineApp/1.1 (Android; Kivy; contact: wiza_nav@example.com)',
                'Accept': 'application/json',
                'Referer': 'https://github.com/wz1310/nav_offline'
            }
            
            geo_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query_text)}&format=json&limit=1"
            
            try:
                req_geo = urllib.request.Request(geo_url, headers=headers)
                with urllib.request.urlopen(req_geo, timeout=15, context=ssl_context) as response:
                    data = json.loads(response.read().decode())
            except Exception as geoe:
                on_error(f"Error Nominatim (Geocoding): {str(geoe)}")
                return
                
            if not data:
                on_error(f"Area tidak ditemukan: {area_name}")
                return
            
            bbox = data[0]['boundingbox']  # [south, north, west, east]
            s, n, w, e = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])

            # 2. Query Overpass API
            on_progress("Mengunduh jaringan jalan (Overpass)...", 0.3)
            overpass_query = f"""
            [out:json][timeout:60];
            (
              way["highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|residential|service"]({s},{w},{n},{e});
            );
            (._;>;);
            out body;
            """
            overpass_url = "https://overpass-api.de/api/interpreter"
            post_data = urllib.parse.urlencode({'data': overpass_query}).encode()
            
            try:
                req_overpass = urllib.request.Request(overpass_url, data=post_data, headers=headers)
                with urllib.request.urlopen(req_overpass, timeout=90, context=ssl_context) as response:
                    osm_data = json.loads(response.read().decode())
            except Exception as ove:
                on_error(f"Error Overpass (Download Jalan): {str(ove)}")
                return

            if 'elements' not in osm_data or not osm_data['elements']:
                on_error("Tidak ada data jalan di area ini.")
                return

            # 3. Build Graph
            on_progress("Membangun graph jaringan jalan...", 0.7)
            G = nx.MultiDiGraph()
            
            nodes = {}
            for el in osm_data['elements']:
                if el['type'] == 'node':
                    nodes[el['id']] = (el['lat'], el['lon'])
                    G.add_node(el['id'], y=el['lat'], x=el['lon'])
            
            for el in osm_data['elements']:
                if el['type'] == 'way':
                    way_nodes = el.get('nodes', [])
                    for i in range(len(way_nodes) - 1):
                        u, v = way_nodes[i], way_nodes[i+1]
                        if u in nodes and v in nodes:
                            dist = haversine(nodes[u][0], nodes[u][1], nodes[v][0], nodes[v][1])
                            G.add_edge(u, v, length=dist)
                            tags = el.get('tags', {})
                            if tags.get('oneway') != 'yes':
                                G.add_edge(v, u, length=dist)

            on_progress("Menyimpan data...", 0.9)
            save_graph(G)

            on_progress("Selesai!", 1.0)
            on_done()

        except Exception as e:
            on_error(f"Gagal: {str(e)}")

    t = threading.Thread(target=_task, daemon=True)
    t.start()
