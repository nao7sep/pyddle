# Created: 2024-02-21
# This script outputs all the available timezones.

import os

os.makedirs("Output", exist_ok=True)
os.chdir("Output")

import zoneinfo

# If no timezones are available, run: pip install tzdata

with open("Output_available_timezones.txt", "w", encoding="utf-8-sig") as file:
    for timezone in sorted(zoneinfo.available_timezones()):
        file.write(timezone + '\n')
        print(timezone)
