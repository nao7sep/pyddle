# Created: 2024-02-29
# This scripts contains debugging-related functions.

import os

import pyddle_path as ppath # pylint: disable=unused-import
# pyddle_path is required for test_path.py.
import pyddle_string as pstring

def is_debugging():
    return pstring.equals_ignore_case(os.getenv('TERM_PROGRAM'), 'vscode') # Must be updated periodically.

# The comments of "exec", which is like a sibling of "eval", contain:
#     In all cases, if the optional parts are omitted, the code is executed in the current scope.

# https://docs.python.org/3/library/functions.html#eval
# https://docs.python.org/3/library/functions.html#exec

def try_evaluate(code):
    try:
        print(f"{code} => {eval(code)}") # pylint: disable=eval-used
        # Needed for testing purposes.

    except Exception as exception: # pylint: disable=broad-except
        print(f"{code} => {exception}")

# For console apps not to close immediately after execution.

def display_press_enter_key_to_continue_if_not_debugging():
    if not is_debugging():
        input("Press Enter key to continue: ")
