"""
Download data OSM per area menggunakan osmnx,
lalu simpan sebagai graph pickle.
"""

import threading
from src.routing import save_graph, DATA_DIR

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


def download_area(area_name: str,
                  on_progress,
                  on_done,
                  on_error) -> None:
    """
    Download graph OSM untuk area tertentu di thread terpisah.

    Args:
        area_name: key dari AREA_OPTIONS
        on_progress: callback(message: str, pct: float)
        on_done: callback()
        on_error: callback(message: str)
    """
    query = AREA_OPTIONS.get(area_name)
    if query is None:
        on_error(f"Area tidak dikenal: {area_name}")
        return

    def _task():
        try:
            import osmnx as ox

            on_progress(f"Menghubungi server OSM…", 0.1)

            # Konfigurasi osmnx — simpan cache di DATA_DIR
            ox.settings.cache_folder = DATA_DIR
            ox.settings.use_cache = True
            ox.settings.log_console = False

            on_progress(f"Mengunduh jaringan jalan: {area_name}…", 0.3)

            G = ox.graph_from_place(
                query,
                network_type="drive",
                simplify=True,
            )

            on_progress("Memproses graph…", 0.7)

            # Pastikan setiap edge punya atribut 'length'
            G = ox.add_edge_lengths(G)

            on_progress("Menyimpan data ke perangkat…", 0.9)
            save_graph(G)

            on_progress("Selesai!", 1.0)
            on_done()

        except ImportError:
            on_error(
                "Library osmnx belum terinstall.\n"
                "Jalankan: pip install osmnx"
            )
        except Exception as e:
            on_error(f"Gagal download: {e}")

    t = threading.Thread(target=_task, daemon=True)
    t.start()
