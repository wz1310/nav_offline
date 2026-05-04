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
import os
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
    R = 6371000 # Radius bumi dalam meter
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def build_graph_from_data(osm_data, area_name, on_progress, on_error):
    """Membangun DiGraph agar mendukung jalan satu arah."""
    try:
        on_progress("Membangun jaringan navigasi...", 0.7)
        # Gunakan DiGraph (Directed) untuk mendukung arah jalan
        G = nx.DiGraph()
        nodes = {el['id']: (el['lat'], el['lon']) for el in osm_data['elements'] if el['type'] == 'node'}
        
        for el in osm_data['elements']:
            if el['type'] == 'way':
                tags = el.get('tags', {})
                # Cek apakah jalan ini satu arah
                oneway = tags.get('oneway') in ['yes', '1', 'true']
                way_nodes = el.get('nodes', [])
                
                for i in range(len(way_nodes) - 1):
                    u, v = way_nodes[i], way_nodes[i+1]
                    if u in nodes and v in nodes:
                        dist = haversine(nodes[u][0], nodes[u][1], nodes[v][0], nodes[v][1])
                        # Tambahkan arah maju
                        G.add_edge(u, v, length=dist)
                        # Jika bukan satu arah, tambahkan arah balik
                        if not oneway:
                            G.add_edge(v, u, length=dist)
        
        if G.number_of_edges() == 0:
            on_error("Data tidak mengandung jaringan jalan yang valid.")
            return

        on_progress("Menyimpan data peta...", 0.9)
        save_graph(G, area_name)
        on_progress("Selesai!", 1.0)
    except Exception as e:
        on_error(f"Gagal memproses data: {str(e)}")

def download_area(area_name, on_progress, on_error):
    query_text = AREA_OPTIONS.get(area_name, area_name)
    
    def _task():
        try:
            # Setup headers yang sudah teruji sukses (menghindari error 406)
            headers = {
                'User-Agent': 'NavigasiIndonesia/1.1',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            # 1. Geocoding via Nominatim
            on_progress("Mencari koordinat area...", 0.1)
            
            if area_name == "Jakarta & sekitarnya":
                bbox = ["-6.3708", "-6.0712", "106.6521", "107.0016"]
                s, n, w, e = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                on_progress("Koordinat Jakarta ditemukan (cached)...", 0.2)
            else:
                geo_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query_text)}&format=json&limit=1"
                try:
                    req_geo = urllib.request.Request(geo_url, headers=headers)
                    with urllib.request.urlopen(req_geo, timeout=15, context=ssl_context) as response:
                        data = json.loads(response.read().decode())
                except Exception as geoe:
                    on_error(f"Error Nominatim: {str(geoe)}")
                    return
                if not data:
                    on_error(f"Area tidak ditemukan: {area_name}")
                    return
                bbox = data[0]['boundingbox']
                s, n, w, e = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])

            # 2. Query Overpass API
            on_progress("Mengunduh jaringan jalan...", 0.3)
            overpass_query = f"""[out:json][timeout:60];(way["highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|residential|service"]({s},{w},{n},{e}););(._;>;);out body;"""
            overpass_url = "https://overpass-api.de/api/interpreter"
            post_data = urllib.parse.urlencode({'data': overpass_query}).encode()
            
            try:
                req_overpass = urllib.request.Request(overpass_url, data=post_data, headers=headers)
                with urllib.request.urlopen(req_overpass, timeout=90, context=ssl_context) as response:
                    osm_data = json.loads(response.read().decode())
            except Exception as ove:
                on_error(f"Error Overpass: {str(ove)}")
                return

            if 'elements' not in osm_data or not osm_data['elements']:
                on_error("Data kosong dari server.")
                return

            # 3. Build & Save
            build_graph_from_data(osm_data, area_name, on_progress, on_error)

        except Exception as e:
            on_error(str(e))

    threading.Thread(target=_task, daemon=True).start()

def import_local_json(file_path, area_name, on_progress, on_error):
    """Fungsi untuk mengimpor file JSON hasil download manual."""
    def _task():
        try:
            on_progress("Membaca file lokal...", 0.2)
            with open(file_path, 'r', encoding='utf-8') as f:
                osm_data = json.load(f)
            
            build_graph_from_data(osm_data, area_name, on_progress, on_error)
        except Exception as e:
            on_error(f"Gagal membaca file: {str(e)}")

    threading.Thread(target=_task, daemon=True).start()
