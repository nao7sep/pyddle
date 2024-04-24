# Created: 2024-03-08
# This script contains globally shared things.

import os

import pyddle_errors as perrors

# ------------------------------------------------------------------------------
#     Main script file path
# ------------------------------------------------------------------------------

# Not a constant, but should act like one.
MAIN_SCRIPT_FILE_PATH: str | None = None

def set_main_script_file_path(file_path):
    # "global" lets us modify the global variables outside of the function.
    # https://www.w3schools.com/python/python_variables_global.asp

    global MAIN_SCRIPT_FILE_PATH # pylint: disable = global-statement
    # Expecting MAIN_SCRIPT_FILE_PATH to work like a field of a class.

    if not os.path.isfile(file_path):
        raise perrors.ArgumentError(f"File not found: {file_path}")

    MAIN_SCRIPT_FILE_PATH = file_path

def get_main_script_file_path():
    """ Raises an error if the main script file path is not set. """

    if not MAIN_SCRIPT_FILE_PATH:
        # If the data's origin is unclear, it could be invalid data.
        # Here, we know how the data must be set, making it the developers' fault.
        raise perrors.InvalidOperationError("Main script file path not set.")

    return MAIN_SCRIPT_FILE_PATH
