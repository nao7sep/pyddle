# Created: 2024-03-04
# This scripts offers a simple key-value store (KVS) using JSON files.

import json
import os
import typing

import pyddle_backup as pbackup
import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_path as ppath

# Lazy loading:
__executing_script_files_directory_path: str | None = None # pylint: disable = invalid-name

def get_executing_script_files_directory_path():
    global __executing_script_files_directory_path # pylint: disable = global-statement

    if not __executing_script_files_directory_path:
        __executing_script_files_directory_path = ppath.dirname(pglobal.get_main_script_file_path())

    return __executing_script_files_directory_path

# Lazy loading:
__public_file_path: str | None = None # pylint: disable = invalid-name

def get_public_file_path():
    global __public_file_path # pylint: disable = global-statement

    if not __public_file_path:
        __public_file_path = os.path.join(get_executing_script_files_directory_path(), ".pyddle_kvs.json")

    return __public_file_path

# Lazy loading:
__private_file_path: str | None = None # pylint: disable = invalid-name

def get_private_file_path():
    global __private_file_path # pylint: disable = global-statement

    if not __private_file_path:
        # https://docs.python.org/3/library/os.path.html#os.path.expanduser
        __private_file_path = os.path.join(os.path.expanduser("~"), ".pyddle_kvs.json")

    return __private_file_path

# Lazy loading:
__public_data: dict[str, typing.Any] | None = None # pylint: disable = invalid-name

def get_public_data():
    global __public_data # pylint: disable = global-statement

    if not __public_data:
        public_file_path = get_public_file_path()

        if os.path.isfile(public_file_path):
            content = pfs.read_all_text_from_file(public_file_path)
            __public_data = json.loads(content)

    return __public_data

# Lazy loading:
__private_data: dict[str, typing.Any] | None = None # pylint: disable = invalid-name

def get_private_data():
    global __private_data # pylint: disable = global-statement

    if not __private_data:
        private_file_path = get_private_file_path()

        if os.path.isfile(private_file_path):
            content = pfs.read_all_text_from_file(private_file_path)
            __private_data = json.loads(content)

    return __private_data

# Lazy loading:
__merged_data: dict[str, typing.Any] | None = None # pylint: disable = invalid-name

def get_merged_data():
    global __merged_data # pylint: disable = global-statement

    if not __merged_data:
        # https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression-in-python
        __merged_data = {
            **get_public_data(),
            **get_private_data()
        }

    return __merged_data

# ------------------------------------------------------------------------------
#     CRUD operations
# ------------------------------------------------------------------------------

# If the key is not in the dictionary, get(key) returns None while [key] raises a KeyError.
# https://docs.python.org/3/library/stdtypes.html#mapping-types-dict

# Important: Keys are compared case-sensitively.
# There seems to be no elegant way (like C#'s IEqualityComparer<T>) to make a case-insensitive dictionary in Python.
# That would be one reason to use only lower-cased keys in JSON files that are meant to be read by Python.

def read_from_public_data(key):
    """ Returns None if the key is not in the dictionary. """

    return get_public_data().get(key)

def read_from_public_data_or_default(key, default_value):
    return get_public_data().get(key, default_value)

def read_from_private_data(key):
    """ Returns None if the key is not in the dictionary. """

    return get_private_data().get(key)

def read_from_private_data_or_default(key, default_value):
    return get_private_data().get(key, default_value)

def read_from_merged_data(key):
    """ Returns None if the key is not in the dictionary. """

    return get_merged_data().get(key)

def read_from_merged_data_or_default(key, default_value):
    return get_merged_data().get(key, default_value)

def update_public_data(key, value):
    get_public_data()[key] = value

    if key not in get_private_data():
        get_merged_data()[key] = value

def update_private_data(key, value):
    get_private_data()[key] = value
    get_merged_data()[key] = value

# In the following code, the same get_* methods may be called multiple times.
# Once the underlying dictionaries have been loaded, the methods are efficient.

def delete_from_public_data(key):
    if key in get_public_data():
        del get_public_data()[key]

    if key in get_merged_data() and key not in get_private_data():
        del get_merged_data()[key]

def delete_from_private_data(key):
    if key in get_private_data():
        del get_private_data()[key]

    if key in get_merged_data() and key not in get_public_data():
        del get_merged_data()[key]

# ------------------------------------------------------------------------------

def save_data_to_file(path, data):
    json_string = json.dumps(data, ensure_ascii = False, indent = 4)
    pfs.write_all_text_to_file(path, json_string)

    # Saves the data to a SQLite database file for backup purposes.
    # This is a "lucky if we have it" kind of backup.
    # It should succeed, but if it doesnt, the program shouldnt crash.
    pbackup.backup("pyddle_kvs", pbackup.ValueType.JSON_STR, json_string, quiet = True)

def save_public_data_to_file():
    save_data_to_file(get_public_file_path(), get_public_data())

def save_private_data_to_file():
    save_data_to_file(get_private_file_path(), get_private_data())
