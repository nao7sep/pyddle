# Created: 2024-02-29
# This scripts contains debugging-related functions.

import os

def is_debugging():
    return os.getenv('TERM_PROGRAM') == 'vscode' # Must be updated periodically.

# For console apps not to close immediately after execution.

def display_press_enter_key_to_continue_if_not_debugging():
    if not is_debugging():
        input("Press Enter key to continue: ")
