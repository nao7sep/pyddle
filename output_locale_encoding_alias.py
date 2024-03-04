# Created: 2024-02-21
# This script outputs all the locale encoding aliases.

import debugging
import file_system
import locale

file_system.make_and_move_to_output_subdirectory()

with open("output_locale_encoding_alias.txt", "w", encoding="utf-8-sig") as file: # Typo preserved.
    for key, value in sorted(locale.locale_encoding_alias.items()):
        file.write(f"{key}: {value}\n")
        print(f"{key}: {value}")

debugging.display_press_enter_key_to_continue_if_not_debugging()
