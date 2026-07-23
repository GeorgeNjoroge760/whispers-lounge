[app]

title = Whispers Lounge
package.name = whisperslounge
package.domain = com.whisperslounge

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,sql
source.include_patterns = database/*,models/*,controllers/*,utils/*,kv/*

version = 1.0.0

requirements = python3,kivy,bcrypt,sqlite3

orientation = portrait

fullscreen = 0

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

android.api = 31
android.minapi = 24
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

android.archs = arm64-v8a

# Bootstrap = sdl2

# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/presplash.png

# androidIFEST.layout = android/AndroidManifest.xml

# p4a.branch = develop

# webview = False

# wakelock = 0

# enable-androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
