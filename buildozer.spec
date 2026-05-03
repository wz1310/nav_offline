[app]
title = Navigasi Indonesia Offline
package.name = navigasiindonesia
package.domain = com.offline.nav

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt

version = 1.0.0

requirements = python3,kivy==2.3.0,osmnx,networkx,requests,certifi,charset-normalizer,idna,urllib3,shapely,pyproj,geopandas,fiona,numpy,pandas

# Orientasi layar
orientation = portrait

# Android permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Android API
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# Arsitektur (arm64-v8a untuk HP modern, armeabi-v7a untuk HP lama)
android.archs = arm64-v8a, armeabi-v7a

# Fullscreen
fullscreen = 0

# Log level (0=error, 1=info, 2=debug)
log_level = 1

[buildozer]
log_level = 1
warn_on_root = 1
