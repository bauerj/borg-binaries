#!/bin/env python3
import requests
import sys
import os

url = "https://api.github.com/repos/borgbackup/borg/releases"

r = requests.get(url).json()
v = r[0]["tag_name"]

old = os.path.exists("/var/volumes/nginx/www/borg_binaries/borg-{}-armv5".format(v))
print(v)
sys.exit(0 if old else 1)
