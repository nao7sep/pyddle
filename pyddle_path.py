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
        Too long file names and potentially harmful partial strings such as ".." are not checked for reasons explained in the comments of this function.
        You can also call contains_invalid_file_name_chars, violates_file_name_rules or is_windows_reserved_file_name individually.
    '''
    # Starting with Windows 10, version 1607, there's an option to remove the MAX_PATH character limit.
    # With it enabled, file names can be up to 32,767 characters long.

    # Although it's safe to assume that the limit is still in effect for most users,
    #     we cant reject a file name that COULD work depending on the user's settings.
    # We must, instead, try/except the file operation and display an error message if it fails.

    # As a file name cant end with a period, ".." alone wont pass the rules.
    # So, somehow injecting "/../" into a file path to access a parent directory is hard enough.
    # But can we say a file name such as "(Unicode chars nobody knows)..(the same)" is guaranteed to be safe?

    # Speaking of Unicode, there's one more thing to consider.

    # ChatGPT:

    # macOS uses a different form of Unicode normalization for filenames compared to most other systems.
    # Specifically, macOS uses NFD (Normalization Form Decomposed) where characters are decomposed into
    # their constituent parts. For example, "é" is stored as "e" + "´". Most other systems use NFC
    # (Normalization Form Composed), where characters are stored in their composed form, so "é" remains "é".

    # This difference can lead to issues when transferring files between macOS and other systems, or when
    # writing cross-platform applications. A filename created on macOS might not match the expected filename
    # on a Linux or Windows system because of this normalization difference.

    # Python's os and pathlib modules may not automatically account for this, leading to potential mismatches
    # when performing file operations based on user input or filenames derived from other systems.

    # A common solution is to explicitly normalize file paths using the unicodedata module in Python when
    # interoperability between macOS and other systems is needed. For instance, converting all paths to NFC
    # before processing them can help ensure consistency across different platforms.

    # ----

    # Because of this, file names via Subversion may mismatch on different platforms,
    #     making the files virtually impossible to be version-controlled.
    # https://stackoverflow.com/questions/55143357/svn-file-names-with-special-characters-%C3%A9%C3%A8%C3%A0
    # This is a major problem for Japanese-speaking people as the language contains a lot of characters that get decomposed.

    # Of course, we must worry about surrogate pairs as well,
    #     especially in an environment where characters are represented as 16-bit values.

    # So, one realistic approach would be:
    #     * If possible, avoid containing user-input strings in file names
    #     * If not, check for widely-known and well-documented things such as
    #           invalid characters, rules violations and reserved names
    #     * Then, always try/except the file operation

    # Additionally:

    # There are dozens of whitespace characters defined in Unicode.
    # https://en.wikipedia.org/wiki/Whitespace_character

    # We also, occasionally, need to deal with right-to-left marks properly.
    # https://en.wikipedia.org/wiki/Right-to-left_mark

    # We cant possibly cover all of these.
    # So, we should do what we can and let the OS's API handle the rest.

    return (not contains_invalid_file_name_chars(file_name) and
            not violates_file_name_rules(file_name) and
            not is_windows_reserved_file_name(file_name))
