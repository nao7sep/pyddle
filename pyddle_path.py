# Created: 2024-03-16
# Contains multi-platform path-related operations.

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
