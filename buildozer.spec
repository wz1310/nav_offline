[app]
title = Navigasi Indonesia Offline
package.name = navigasiindonesia
package.domain = com.offline.nav

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
source.exclude_dirs = data,tests,.git,.github,__pycache__

version = 1.0.0

# Requirements — hanya yang benar-benar dibutuhkan saat runtime di Android
# osmnx & networkx dipakai untuk download + routing
requirements = python3,kivy==2.3.0,osmnx,networkx,requests,certifi,charset-normalizer,idna,urllib3,shapely,pyproj,numpy,pandas,fiona,geopandas

# Orientasi
orientation = portrait

# Android permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Android API
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# Hanya arm64 dulu untuk mempercepat build
android.archs = arm64-v8a

# Gradle
android.gradle_dependencies =

# Fullscreen
fullscreen = 0

# Log
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
