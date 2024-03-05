# Created: 2024-02-21
# This script outputs all the available timezones.

import pyddle_lib.pyddle_debugging as debugging
import pyddle_lib.pyddle_file_system as file_system
import zoneinfo

file_system.make_and_move_to_output_subdirectory()

# If no timezones are available, run: pip3/pip install tzdata

with file_system.open_file_and_write_utf_encoding_bom("output_available_timezones.txt") as file:
    for timezone in sorted(zoneinfo.available_timezones()):
        file.write(timezone + '\n')
        print(timezone)

debugging.display_press_enter_key_to_continue_if_not_debugging()
