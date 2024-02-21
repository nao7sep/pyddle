﻿# Created: 2024-02-21
# This script outputs all the locale encoding aliases.

import os

os.makedirs("Output", exist_ok=True)
os.chdir("Output")

import locale

with open("Output_locale_encoding_alias.txt", "w", encoding="utf-8-sig") as file: # Typo preserved.
    for key, value in sorted(locale.locale_encoding_alias.items()):
        file.write(f"{key}: {value}\n")
        print(f"{key}: {value}")
