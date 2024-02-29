# Created: 2024-02-21
# This script outputs all the locale encoding aliases.

from file_system import make_and_move_to_output_subdirectory

make_and_move_to_output_subdirectory()

import locale

with open("output_locale_encoding_alias.txt", "w", encoding="utf-8-sig") as file: # Typo preserved.
    for key, value in sorted(locale.locale_encoding_alias.items()):
        file.write(f"{key}: {value}\n")
        print(f"{key}: {value}")

from debugging import display_press_enter_key_to_continue_if_not_debugging

display_press_enter_key_to_continue_if_not_debugging()
