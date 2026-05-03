# Navigasi Indonesia Offline

Aplikasi navigasi offline untuk Indonesia berbasis Python + Kivy.

## Fitur
- Download data peta OSM per kota/area sekali saja
- Routing offline setelah data diunduh
- Visualisasi rute di browser via Leaflet.js
- Build APK via GitHub Actions

## Cara Pakai (Desktop / Testing)

```bash
pip install -r requirements.txt
python main.py
```

## Build APK

### Via GitHub Actions (recommended)
1. Push kode ke GitHub
2. Buka tab **Actions** di repo
3. Pilih workflow **Build Android APK**
4. Klik **Run workflow**
5. Setelah selesai (~30–45 menit), download APK dari tab **Artifacts**

### Manual (Linux only)
```bash
pip install buildozer cython==0.29.37
buildozer android debug
```
APK ada di folder `bin/`.

## Struktur Project

```
├── main.py                    # Entry point
├── buildozer.spec             # Konfigurasi build APK
├── requirements.txt           # Dependencies Python
├── .github/workflows/
│   └── build.yml              # GitHub Actions workflow
└── src/
    ├── routing.py             # Load graph & hitung rute
    ├── downloader.py          # Download data OSM
    ├── download_screen.py     # UI layar download
    └── map_screen.py          # UI layar navigasi
```

## Area yang Tersedia
- Jakarta & sekitarnya
- Bandung & sekitarnya
- Surabaya & sekitarnya
- Medan & sekitarnya
- Makassar & sekitarnya
- Yogyakarta & sekitarnya
- Semarang & sekitarnya
- Bali (Denpasar)
