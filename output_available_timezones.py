# Created: 2024-02-21
# This script outputs all the available timezones.

import debugging
import file_system
import zoneinfo

file_system.make_and_move_to_output_subdirectory()

# If no timezones are available, run: pip3/pip install tzdata

with open("output_available_timezones.txt", "w", encoding="utf-8-sig") as file:
    for timezone in sorted(zoneinfo.available_timezones()):
        file.write(timezone + '\n')
        print(timezone)

debugging.display_press_enter_key_to_continue_if_not_debugging()
