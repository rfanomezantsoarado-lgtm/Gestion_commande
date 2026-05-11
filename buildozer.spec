[app]

# Application info
title = Gestion commande EN
package.name = gestion_commande_en
package.domain = org.en

# Source files
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,db

# Version
version = 0.1

# Requirements
requirements = python3,kivy,reportlab,pyjnius

# Orientation
orientation = portrait

# Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# Accept SDK license
android.accept_sdk_license = True

# Fullscreen
fullscreen = 0

# Presplash
# presplash.filename = %(source.dir)s/presplash.png

# Icon
# icon.filename = %(source.dir)s/icon.png

# Allow overriding of the default Android log capture
# log_level = 2

# Supported architectures
android.archs = arm64-v8a, armeabi-v7a