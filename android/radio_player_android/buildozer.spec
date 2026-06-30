[app]  
title = Radio Player  
package.name = radioplayer  
package.domain = org.radioplayer  
source.dir = .  
source.include_exts = py,png,jpg,kv,atlas,ttf,json  
version = 1.0  
requirements = python3,kivy==2.3.0,kivymd==1.1.1,requests,urllib3  
orientation = portrait  
fullscreen = 1  
android.api = 33  
android.minapi = 21  
android.ndk = 27b  
android.permissions = INTERNET, READ_MEDIA_AUDIO, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE  
android.archs = arm64-v8a  
p4a.branch = v2024.01.21  
log_level = 2 
source.exclude_exts = spec  
source.exclude_dirs = tests, bin, .buildozer  
source.exclude_patterns = buildozer.spec, *.pyc, .gitignore  
android.accept_sdk_license = True  
android.auto_sdk = True  
android.auto_ndk = True 
