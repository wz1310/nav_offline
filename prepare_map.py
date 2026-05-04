import osmnx as ox
import pickle
import os

"""
Script untuk menyiapkan data peta offline di PC/WSL sebelum mem-build APK.
Cara pakai:
1. Pastikan osmnx terinstall: pip install osmnx networkx==3.1
2. Jalankan: python prepare_map.py
3. File .graph akan muncul di folder data/ dan siap di-bundle ke APK.
"""

def prepare_jakarta():
    print("Sedang mengunduh data Jakarta (ini mungkin butuh beberapa menit)...")
    try:
        # Download jaringan jalan menggunakan OSMnx (hanya di PC)
        G = ox.graph_from_place("Jakarta, Indonesia", network_type="drive")

        # Pastikan folder data ada
        os.makedirs("data", exist_ok=True)

        # Simpan ke format yang dimengerti aplikasi (.graph)
        filepath = os.path.join("data", "Jakarta & sekitarnya.graph")
        with open(filepath, "wb") as f:
            pickle.dump(G, f)

        print(f"Selesai! File peta telah dibuat di: {filepath}")
        print("Sekarang Anda bisa mem-build APK dan peta ini akan otomatis terbawa.")
    except Exception as e:
        print(f"Gagal mengunduh peta: {e}")

if __name__ == "__main__":
    prepare_jakarta()
