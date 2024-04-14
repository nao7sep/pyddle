# Created: 2024-03-02
# This script outputs all environment variables and their values.

import os

import pyddle_console as pconsole
import pyddle_debugging as pdebugging
import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

main_separator = '' # pylint: disable=invalid-name
other_separators = [] # pylint: disable=invalid-name

# On Windows, the most commonly used separator seems to be ';'.
# On Mac, it seems to be ':'.
# There MAY be an app that uses ',' in its environment variables.
# Out of the 3, we look for what's not the most commonly used one on each platform,
#     excluding ':', which frequently appears in paths on Windows.

if pstring.equals_ignore_case(os.name, 'nt'):
    main_separator = ';' # pylint: disable=invalid-name
    other_separators = [',']

else:
    main_separator = ':' # pylint: disable=invalid-name
    other_separators = [';', ',']

is_first_variable = True # pylint: disable=invalid-name

pfs.make_and_move_to_output_subdirectory()

with pfs.open_file_and_write_utf_encoding_bom("output_environment_variables.txt") as file:
    for key, value in sorted(os.environ.items()):
        separated_values = [separated_value for separated_value in value.split(main_separator) if separated_value] # Works like len(separated_value) > 0.

        if is_first_variable:
            is_first_variable = False # pylint: disable=invalid-name

        else:
            file.write("\n")
            print()

        file.write(f"[{key}]\n")
        print(f"[{key}]")

        is_path = pstring.equals_ignore_case(key, "PATH") # Case-insensitively, just in case.

        if pdebugging.is_debugging():
            if any(separator in value for separator in other_separators):
                pconsole.print("Contains another separator.", colors = pconsole.WARNING_COLORS) # Worth investigating.

        if separated_values:
            for separated_value in separated_values:
                file.write(f"{separated_value}\n")

                if is_path and not os.path.isdir(separated_value):
                    pconsole.print(separated_value, colors = pconsole.WARNING_COLORS) # Missing directory.
                    # We could also look for duplicates,
                    #     but on Windows for example, each user's environment variables are merged with the system's,
                    #     and we wouldnt always know which ones must be preserved.

                else:
                    print(separated_value)

        else:
            file.write("(Empty)\n")
            pconsole.print("(Empty)", colors = pconsole.WARNING_COLORS) # Not necessary an error.

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
