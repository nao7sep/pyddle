# Created: 2024-03-02
# This script outputs all environment variables and their values.

from debugging import is_debugging

other_possible_separators = [','] # ';' seems to be the most commonly used separator.

import os

is_first_variable = True

from file_system import make_and_move_to_output_subdirectory

make_and_move_to_output_subdirectory()

with open("output_environment_variables.txt", "w", encoding="utf-8-sig") as file:
    for key, value in os.environ.items():
        if is_debugging():
            if any(separator in value for separator in other_possible_separators):
                print(f"Contains another possible separator: {key} = {value}")
                continue
        separated_values = [separated_value for separated_value in value.split(';') if separated_value] # Works like len(separated_value) > 0.
        if is_first_variable:
            is_first_variable = False
        else:
            file.write("\n")
            print()
        file.write(f"[{key}]\n")
        print(f"[{key}]")
        for separated_value in separated_values:
            file.write(f"{separated_value}\n")
            print(separated_value)

from debugging import display_press_enter_key_to_continue_if_not_debugging

display_press_enter_key_to_continue_if_not_debugging()
