# Created: 2024-02-29
# This scripts contains debugging-related functions.

import os
import pyddle_path # Required for test_path.py.
import pyddle_string

def is_debugging():
    return pyddle_string.equals_ignore_case(os.getenv('TERM_PROGRAM'), 'vscode') # Must be updated periodically.

def try_evaluate(code):
    try:
        print(f"{code} => {eval(code)}")

    except Exception as exception:
        print(f"{code} => {exception}")

# For console apps not to close immediately after execution.

def display_press_enter_key_to_continue_if_not_debugging():
    if not is_debugging():
        input("Press Enter key to continue: ")
