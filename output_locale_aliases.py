# Created: 2024-02-21
# This script outputs all the locale aliases.

from file_system import make_and_move_to_output_subdirectory

make_and_move_to_output_subdirectory()

import locale

with open("output_locale_aliases.txt", "w", encoding="utf-8-sig") as file: # Write the BOM.
    for key, value in sorted(locale.locale_alias.items()):
        file.write(f"{key}: {value}\n") # The line ending will be converted to the default one for the platform.
        print(f"{key}: {value}")

from debugging import display_press_enter_key_to_continue_if_not_debugging

display_press_enter_key_to_continue_if_not_debugging()
