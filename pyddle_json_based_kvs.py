# Created: 2024-03-04
# This scripts offers a simple key-value store (KVS) using JSON files.

import datetime
import json
import os
import pyddle_file_system as file_system
import sqlite3

# https://docs.python.org/3/reference/datamodel.html#modules
executing_script_files_directory_path = os.path.dirname(__file__)
first_kvs_file_path = os.path.join(executing_script_files_directory_path, ".pyddle_kvs.json")

# https://docs.python.org/3/library/os.path.html#os.path.expanduser
second_kvs_file_path = os.path.join(os.path.expanduser("~"), ".pyddle_kvs.json")

first_kvs_data = {}

if os.path.isfile(first_kvs_file_path):
    content = file_system.read_all_text_from_file(first_kvs_file_path)
    first_kvs_data = json.loads(content)

second_kvs_data = {}

if os.path.isfile(second_kvs_file_path):
    content = file_system.read_all_text_from_file(second_kvs_file_path)
    second_kvs_data = json.loads(content)

merged_kvs_data = {**first_kvs_data, **second_kvs_data}

def display_merged_kvs_data():
    print("Merged KVS data:")

    for key, value in merged_kvs_data.items():
        print(f"    {key}: {value}")

# ------------------------------------------------------------------------------
#     CRUD operations
# ------------------------------------------------------------------------------

# If the key is not in the dictionary, get(key) returns None while [key] raises a KeyError.
# https://docs.python.org/3/library/stdtypes.html#mapping-types-dict

def read_from_first_kvs_data(key):
    return first_kvs_data.get(key)

def read_from_first_kvs_data_or_default(key, default_value):
    return first_kvs_data.get(key, default_value)

def read_from_second_kvs_data(key):
    return second_kvs_data.get(key)

def read_from_second_kvs_data_or_default(key, default_value):
    return second_kvs_data.get(key, default_value)

def read_from_merged_kvs_data(key):
    return merged_kvs_data.get(key)

def read_from_merged_kvs_data_or_default(key, default_value):
    return merged_kvs_data.get(key, default_value)

def update_first_kvs_data(key, value):
    first_kvs_data[key] = value

    if key not in second_kvs_data:
        merged_kvs_data[key] = value

def update_second_kvs_data(key, value):
    second_kvs_data[key] = value
    merged_kvs_data[key] = value

def delete_from_first_kvs_data(key):
    if key in first_kvs_data:
        del first_kvs_data[key]

    if key in merged_kvs_data and key not in second_kvs_data:
        del merged_kvs_data[key]

def delete_from_second_kvs_data(key):
    if key in second_kvs_data:
        del second_kvs_data[key]

    if key in merged_kvs_data and key not in first_kvs_data:
        del merged_kvs_data[key]

# ------------------------------------------------------------------------------

def save_kvs_data_to_file(path, data):
    json_string = json.dumps(data, indent=4)
    file_system.write_all_text_to_file(path, json_string)

    root, _ = os.path.splitext(path)
    db_file_path = root + ".db"

    with sqlite3.connect(db_file_path) as connection:
        cursor = connection.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS pyddle_kvs_strings ("
                           "utc DATETIME NOT NULL, "
                           "string TEXT NOT NULL)")

        cursor.execute("INSERT INTO pyddle_kvs_strings (utc, string) "
                           "VALUES (?, ?)",
                           (datetime.datetime.now(datetime.UTC), json_string))

        connection.commit()

def save_first_kvs_data_to_file():
    save_kvs_data_to_file(first_kvs_file_path, first_kvs_data)

def save_second_kvs_data_to_file():
    save_kvs_data_to_file(second_kvs_file_path, second_kvs_data)
