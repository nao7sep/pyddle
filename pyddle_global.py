# Created: 2024-03-08
# This script contains globally shared things and therefore must be imported first.

# Dont import anything else.
import os
# Dont import anything else.

# ------------------------------------------------------------------------------
#     Main script file path
# ------------------------------------------------------------------------------

MAIN_SCRIPT_FILE_PATH = None

def set_main_script_file_path(file_path):
    # "global" lets us modify the global variables outside of the function.
    # https://www.w3schools.com/python/python_variables_global.asp

    global MAIN_SCRIPT_FILE_PATH # pylint: disable=global-statement
    # Expecting MAIN_SCRIPT_FILE_PATH to work like a field of a class.

    if not os.path.isfile(file_path):
        raise RuntimeError(f"File not found: {file_path}")

    MAIN_SCRIPT_FILE_PATH = file_path

def get_main_script_file_path():
    """ Raises a RuntimeError if the main script file path is not set. """

    if not MAIN_SCRIPT_FILE_PATH:
        raise RuntimeError("Main script file path not set.")

    return MAIN_SCRIPT_FILE_PATH
