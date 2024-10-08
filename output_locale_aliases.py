﻿# Created: 2024-02-21
# This script outputs all the locale aliases.

import locale

import pyddle_debugging as pdebugging
import pyddle_file_system as pfs
import pyddle_global as pglobal

pglobal.set_main_script_file_path(__file__)

pfs.make_and_move_to_output_subdirectory()

with pfs.open_file_and_write_utf_encoding_bom("output_locale_aliases.txt") as file:
    for key, value in sorted(locale.locale_alias.items()):
        file.write(f"{key}: {value}\n") # The line ending will be converted to the default one for the platform.
        print(f"{key}: {value}")

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
