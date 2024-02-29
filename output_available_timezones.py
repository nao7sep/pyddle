# Created: 2024-02-21
# This script outputs all the available timezones.

from file_system import make_and_move_to_output_subdirectory

make_and_move_to_output_subdirectory()

import zoneinfo

# If no timezones are available, run: pip install tzdata

with open("output_available_timezones.txt", "w", encoding="utf-8-sig") as file:
    for timezone in sorted(zoneinfo.available_timezones()):
        file.write(timezone + '\n')
        print(timezone)

from debugging import display_press_enter_key_to_continue_if_not_debugging

display_press_enter_key_to_continue_if_not_debugging()
