# Created: 2024-02-21
# This script outputs all the locale aliases.

import debugging
import file_system
import locale

file_system.make_and_move_to_output_subdirectory()

with open("output_locale_aliases.txt", "w", encoding="utf-8-sig") as file: # Write the BOM.
    for key, value in sorted(locale.locale_alias.items()):
        file.write(f"{key}: {value}\n") # The line ending will be converted to the default one for the platform.
        print(f"{key}: {value}")

debugging.display_press_enter_key_to_continue_if_not_debugging()
