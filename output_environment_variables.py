﻿# Created: 2024-03-02
# This script outputs all environment variables and their values.

import os
import pyddle_console as console
import pyddle_debugging as debugging
import pyddle_file_system as file_system
import pyddle_string as string

main_separator = ''
other_separators = []

# On Windows, the most commonly used separator seems to be ';'.
# On Mac, it seems to be ':'.
# There MAY be an app that uses ',' in its environment variables.
# Out of the 3, we look for what's not the most commonly used one on each platform,
#     excluding ':', which frequently appears in paths on Windows.

if string.equals_ignore_case(os.name, 'nt'):
    main_separator = ';'
    other_separators = [',']

else:
    main_separator = ':'
    other_separators = [';', ',']

is_first_variable = True

file_system.make_and_move_to_output_subdirectory()

with file_system.open_file_and_write_utf_encoding_bom("output_environment_variables.txt") as file:
    for key, value in sorted(os.environ.items()):
        separated_values = [separated_value for separated_value in value.split(main_separator) if separated_value] # Works like len(separated_value) > 0.

        if is_first_variable:
            is_first_variable = False

        else:
            file.write("\n")
            print()

        file.write(f"[{key}]\n")
        print(f"[{key}]")

        is_path = string.equals_ignore_case(key, "PATH") # Case-insensitively, just in case.

        if debugging.is_debugging():
            if any(separator in value for separator in other_separators):
                console.print_warning("Contains another separator.") # Worth investigating.

        if separated_values:
            for separated_value in separated_values:
                file.write(f"{separated_value}\n")

                if is_path and not os.path.isdir(separated_value):
                    console.print_warning(separated_value) # Missing directory.
                    # We could also look for duplicates,
                    #     but on Windows for example, each user's environment variables are merged with the system's,
                    #     and we wouldnt always know which ones must be preserved.

                else:
                    print(separated_value)

        else:
            file.write("(Empty)\n")
            console.print_warning("(Empty)") # Not necessary an error.

debugging.display_press_enter_key_to_continue_if_not_debugging()
