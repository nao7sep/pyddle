﻿# Created: 2024-02-21
# This script outputs all the available timezones.

import zoneinfo

import pyddle_debugging as pdebugging
import pyddle_file_system as pfs
import pyddle_global as pglobal

pglobal.set_main_script_file_path(__file__)

pfs.make_and_move_to_output_subdirectory()

# If no timezones are available, run: pip3/pip install tzdata

with pfs.open_file_and_write_utf_encoding_bom("output_available_timezones.txt") as file:
    for timezone in sorted(zoneinfo.available_timezones()):
        file.write(timezone + '\n')
        print(timezone)

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
