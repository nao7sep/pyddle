# Created: 2024-03-04
# This scripts offers a simple key-value store (KVS) using JSON files.

import datetime
import json
import os
import sqlite3

import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_path as ppath

# Lazy loading:
__executing_script_files_directory_path = None # pylint: disable = invalid-name

def get_executing_script_files_directory_path():
    global __executing_script_files_directory_path # pylint: disable = global-statement

    if not __executing_script_files_directory_path:
        __executing_script_files_directory_path = ppath.dirname(pglobal.get_main_script_file_path())

    return __executing_script_files_directory_path

# Lazy loading:
__first_kvs_file_path = None # pylint: disable = invalid-name

def get_first_kvs_file_path():
    global __first_kvs_file_path # pylint: disable = global-statement

    if not __first_kvs_file_path:
        __first_kvs_file_path = os.path.join(get_executing_script_files_directory_path(), ".pyddle_kvs.json")

    return __first_kvs_file_path

# Lazy loading:
__second_kvs_file_path = None # pylint: disable = invalid-name

def get_second_kvs_file_path():
    global __second_kvs_file_path # pylint: disable = global-statement

    if not __second_kvs_file_path:
        # https://docs.python.org/3/library/os.path.html#os.path.expanduser
        __second_kvs_file_path = os.path.join(os.path.expanduser("~"), ".pyddle_kvs.json")

    return __second_kvs_file_path

# Lazy loading:
__first_kvs_data = None # pylint: disable = invalid-name

def get_first_kvs_data():
    global __first_kvs_data # pylint: disable = global-statement

    if not __first_kvs_data:
        first_kvs_file_path = get_first_kvs_file_path()

        if os.path.isfile(first_kvs_file_path):
            content = pfs.read_all_text_from_file(first_kvs_file_path)
            __first_kvs_data = json.loads(content)

    return __first_kvs_data

# Lazy loading:
__second_kvs_data = None # pylint: disable = invalid-name

def get_second_kvs_data():
    global __second_kvs_data # pylint: disable = global-statement

    if not __second_kvs_data:
        second_kvs_file_path = get_second_kvs_file_path()

        if os.path.isfile(second_kvs_file_path):
            content = pfs.read_all_text_from_file(second_kvs_file_path)
            __second_kvs_data = json.loads(content)

    return __second_kvs_data

# Lazy loading:
__merged_kvs_data = None # pylint: disable = invalid-name

def get_merged_kvs_data():
    global __merged_kvs_data # pylint: disable = global-statement

    if not __merged_kvs_data:
        # https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression-in-python
        __merged_kvs_data = {
            **get_first_kvs_data(),
            **get_second_kvs_data()
        }

    return __merged_kvs_data

# ------------------------------------------------------------------------------
#     CRUD operations
# ------------------------------------------------------------------------------

# If the key is not in the dictionary, get(key) returns None while [key] raises a KeyError.
# https://docs.python.org/3/library/stdtypes.html#mapping-types-dict

# Important: Keys are compared case-sensitively.
# There seems to be no elegant way (like C#'s IEqualityComparer<T>) to make a case-insensitive dictionary in Python.
# That would be one reason to use only lower-cased keys in JSON files that are meant to be read by Python.

def read_from_first_kvs_data(key):
    """ Returns None if the key is not in the dictionary. """

    return get_first_kvs_data().get(key)

def read_from_first_kvs_data_or_default(key, default_value):
    return get_first_kvs_data().get(key, default_value)

def read_from_second_kvs_data(key):
    """ Returns None if the key is not in the dictionary. """

    return get_second_kvs_data().get(key)

def read_from_second_kvs_data_or_default(key, default_value):
    return get_second_kvs_data().get(key, default_value)

def read_from_merged_kvs_data(key):
    """ Returns None if the key is not in the dictionary. """

    return get_merged_kvs_data().get(key)

def read_from_merged_kvs_data_or_default(key, default_value):
    return get_merged_kvs_data().get(key, default_value)

def update_first_kvs_data(key, value):
    get_first_kvs_data()[key] = value

    if key not in get_second_kvs_data():
        get_merged_kvs_data()[key] = value

def update_second_kvs_data(key, value):
    get_second_kvs_data()[key] = value
    get_merged_kvs_data()[key] = value

# In the following code, the same get_* methods may be called multiple times.
# Once the underlying dictionaries have been loaded, the methods are efficient.

def delete_from_first_kvs_data(key):
    if key in get_first_kvs_data():
        del get_first_kvs_data()[key]

    if key in get_merged_kvs_data() and key not in get_second_kvs_data():
        del get_merged_kvs_data()[key]

def delete_from_second_kvs_data(key):
    if key in get_second_kvs_data():
        del get_second_kvs_data()[key]

    if key in get_merged_kvs_data() and key not in get_first_kvs_data():
        del get_merged_kvs_data()[key]

# ------------------------------------------------------------------------------

def save_kvs_data_to_file(path, data):
    json_string = json.dumps(data, ensure_ascii = False, indent=4)
    pfs.write_all_text_to_file(path, json_string)

    # Saves the data to a SQLite database file for backup purposes.
    # This is a "lucky if we have it" kind of backup.
    # It should succeed, but if it doesnt, the program shouldnt crash.

    try:
        root, _ = os.path.splitext(path)
        db_file_path = root + ".db"

        with sqlite3.connect(db_file_path) as connection:
            cursor = connection.cursor()

            cursor.execute("CREATE TABLE IF NOT EXISTS pyddle_kvs_strings ("
                            "utc DATETIME NOT NULL, "
                            "string TEXT NOT NULL)")

            cursor.execute("INSERT INTO pyddle_kvs_strings (utc, string) "
                            "VALUES (?, ?)",
                            (datetime.datetime.now(datetime.UTC).isoformat(), json_string))

            connection.commit()

    except Exception: # pylint: disable = broad-except
        pass

def save_first_kvs_data_to_file():
    save_kvs_data_to_file(get_first_kvs_file_path(), get_first_kvs_data())

def save_second_kvs_data_to_file():
    save_kvs_data_to_file(get_second_kvs_file_path(), get_second_kvs_data())
