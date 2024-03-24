# Created: 2024-03-16
# Contains multi-platform path-related operations.

import os
import pyddle_string as string

# os.path.basename(), os.path.dirname(), os.path.splitext() (and some more) are not available as static methods in pathlib.
# https://docs.python.org/3/library/pathlib.html#correspondence-to-tools-in-the-os-module

# Ouf of the three, according to the results of test_path.py,
#     we should probably avoid using os.path.basename() and os.path.dirname().

def basename(path):
    index = string.last_index_of_any(path, ['\\', '/'])

    if index >= 0:
        return path[index + 1 :]

    return path

def dirname(path):
    index = string.last_index_of_any(path, ['\\', '/'])

    if index >= 0:
        return path[: index]

    return ""

# ------------------------------------------------------------------------------
#     Minimal validation
# ------------------------------------------------------------------------------

# https://stackoverflow.com/questions/1976007/what-characters-are-forbidden-in-windows-and-linux-directory-names
# https://gist.github.com/doctaphred/d01d05291546186941e1b7ddc02034d3
# https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file

# < (less than)
# > (greater than)
# : (colon)
# " (double quote)
# / (forward slash)
# \ (backslash)
# | (vertical bar or pipe)
# ? (question mark)
# * (asterisk)

# Integer value zero, sometimes referred to as the ASCII NUL character.
# Characters whose integer representations are in the range from 1 through 31.

invalid_file_name_chars = "<>:\"/\\|?*"

def contains_invalid_file_name_chars(file_name):
    for char in file_name:
        if char in invalid_file_name_chars or (0 <= ord(char) <= 31):
            return True

    return False

# Do not end a file or directory name with a space or a period.

def violates_file_name_rules(file_name):
    return file_name.endswith(" ") or file_name.endswith(".")

# CON, PRN, AUX, NUL,
#     COM0, COM1, COM2, COM3, COM4, COM5, COM6, COM7, COM8, COM9, COM¹, COM², COM³,
#     LPT0, LPT1, LPT2, LPT3, LPT4, LPT5, LPT6, LPT7, LPT8, LPT9, LPT¹, LPT², and LPT³.
# Also avoid these names followed immediately by an extension;
#     for example, NUL.txt and NUL.tar.gz are both equivalent to NUL.

windows_reserved_file_names = [
    ["AUX", "CON", "NUL", "PRN"],
    ["COM0", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "COM¹", "COM²", "COM³"],
    ["LPT0", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9", "LPT¹", "LPT²", "LPT³"]
]

def is_windows_reserved_file_name(file_name):
    root, _ = os.path.splitext(file_name)
    length = len(root)

    if length == 3:
        for reserved_file_name in windows_reserved_file_names[0]:
            if string.equals_ignore_case(root, reserved_file_name):
                return True

    elif length == 4:
        if string.startswith_ignore_case(root, "C"):
            for reserved_file_name in windows_reserved_file_names[1]:
                if string.equals_ignore_case(root, reserved_file_name):
                    return True

        elif string.startswith_ignore_case(root, "L"):
            for reserved_file_name in windows_reserved_file_names[2]:
                if string.equals_ignore_case(root, reserved_file_name):
                    return True

    return False

def is_valid_file_name(file_name):
    '''
        Too long file names and potentially harmful partial strings such as ".." are not checked for reasons explained in XY44 File Name Validation.json.
        You can also call contains_invalid_file_name_chars, violates_file_name_rules or is_windows_reserved_file_name individually.
    '''
    # The comments have been moved to: XY44 File Name Validation.json
    # I believe some parts were useful, but they, as a whole, were highly disoriented.

    return (not contains_invalid_file_name_chars(file_name) and
            not violates_file_name_rules(file_name) and
            not is_windows_reserved_file_name(file_name))
