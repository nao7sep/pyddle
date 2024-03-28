# Created: 2024-03-08
# This script contains things that must be initialized first and therefore must be imported first.

# DONT import anything from pyddle in this script.
import os
import pyddle_path # path is a too common name.

# ------------------------------------------------------------------------------
#     Main script file path
# ------------------------------------------------------------------------------

main_script_file_path = ""
main_script_file_name = ""
main_script_file_name_without_extension = ""
main_script_file_extension = ""

def set_main_script_file_path(file_path):
    global main_script_file_path
    global main_script_file_name
    global main_script_file_name_without_extension
    global main_script_file_extension

    if not os.path.isfile(file_path):
        raise RuntimeError(f"File not found: {file_path}")

    main_script_file_path = file_path
    main_script_file_name = pyddle_path.basename(file_path)
    main_script_file_name_without_extension, main_script_file_extension = os.path.splitext(main_script_file_name)

def get_main_script_file_path():
    """ Raises a RuntimeError if the main script file path is not set. """

    if not main_script_file_path:
        raise RuntimeError("Main script file path not set.")

    return main_script_file_path

def get_main_script_file_name():
    """ Raises a RuntimeError if the main script file name is not set. """

    if not main_script_file_name:
        raise RuntimeError("Main script file name not set.")

    return main_script_file_name

def get_main_script_file_name_without_extension():
    """ Raises a RuntimeError if the main script file name without extension is not set. """

    if not main_script_file_name_without_extension:
        raise RuntimeError("Main script file name without extension not set.")

    return main_script_file_name_without_extension

def get_main_script_file_extension():
    """ Raises a RuntimeError if the main script file extension is not set. """

    if not main_script_file_extension:
        raise RuntimeError("Main script file extension not set.")

    return main_script_file_extension
