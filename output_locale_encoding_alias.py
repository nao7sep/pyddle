# Created: 2024-02-21
# This script outputs all the locale encoding aliases.

import locale
import pyddle_lib.debugging as debugging
import pyddle_lib.file_system as file_system

file_system.make_and_move_to_output_subdirectory()

with file_system.open_file_and_write_utf_encoding_bom("output_locale_encoding_alias.txt") as file: # Typo preserved.
    for key, value in sorted(locale.locale_encoding_alias.items()):
        file.write(f"{key}: {value}\n")
        print(f"{key}: {value}")

debugging.display_press_enter_key_to_continue_if_not_debugging()
