# Created: 2024-03-08
# This script contains things that must be initialized first and therefore must be imported first.

# DONT import anything else.
import os

# ------------------------------------------------------------------------------
#     Main script file path
# ------------------------------------------------------------------------------

main_script_file_path = None

def set_main_script_file_path(file_path):
    # "global" lets us modify the global variables outside of the function.
    # https://www.w3schools.com/python/python_variables_global.asp

    global main_script_file_path

    if not os.path.isfile(file_path):
        raise RuntimeError(f"File not found: {file_path}")

    main_script_file_path = file_path

def get_main_script_file_path():
    """ Raises a RuntimeError if the main script file path is not set. """

    if not main_script_file_path:
        raise RuntimeError("Main script file path not set.")

    return main_script_file_path
