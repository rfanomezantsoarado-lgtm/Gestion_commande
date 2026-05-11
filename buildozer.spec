[app]
title = Gestion commande EN
package.name = gestion_commande_en
package.domain = org.en

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,db

version = 0.1

requirements = python3,kivy,reportlab,sqlite3,android

orientation = portrait

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

fullscreen = 0
android.api = 33
android.minapi = 21
android.ndk = 23b