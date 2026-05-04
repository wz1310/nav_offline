[app]
title = Navigasi Indonesia Offline
package.name = navigasiindonesia
package.domain = com.offline.nav

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
source.exclude_dirs = data,tests,.git,.github,__pycache__

version = 1.0.0

requirements = python3,kivy==2.3.0,networkx,requests,certifi,charset-normalizer,idna,urllib3

orientation = portrait

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21

# Gunakan build-tools yang sudah di-install di step sebelumnya
android.build_tools_version = 33.0.2

# Hanya arm64 untuk mempercepat build
android.archs = arm64-v8a

fullscreen = 0

log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
