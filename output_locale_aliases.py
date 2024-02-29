# Created: 2024-02-21
# This script outputs all the locale aliases.

import os

os.makedirs("output", exist_ok=True)
os.chdir("output")

import locale

with open("output_locale_aliases.txt", "w", encoding="utf-8-sig") as file: # Write the BOM.
    for key, value in sorted(locale.locale_alias.items()):
        file.write(f"{key}: {value}\n") # The line ending will be converted to the default one for the platform.
        print(f"{key}: {value}")
