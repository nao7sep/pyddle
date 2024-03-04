# Created: 2024-03-04
# This scripts offers a simple key-value store (KVS) using JSON files.

import os

# https://docs.python.org/3/reference/datamodel.html#modules
executing_script_files_directory_path = os.path.dirname(__file__)
first_kvs_file_path = os.path.join(executing_script_files_directory_path, ".pyddle_kvs.json")
print(first_kvs_file_path)

# https://docs.python.org/3/library/os.path.html#os.path.expanduser
second_kvs_file_path = os.path.join(os.path.expanduser("~"), ".pyddle_kvs.json")
print(second_kvs_file_path)

import json

first_kvs_data = {}

if os.path.isfile(first_kvs_file_path):
    with open(first_kvs_file_path, "r") as file:
        first_kvs_data = json.load(file)

second_kvs_data = {}

if os.path.isfile(second_kvs_file_path):
    with open(second_kvs_file_path, "r") as file:
        second_kvs_data = json.load(file)

merged_kvs_data = {**first_kvs_data, **second_kvs_data}

def show_merged_kvs_data():
    print("Merged KVS data:")

    for key, value in merged_kvs_data.items():
        print(f"    {key}: {value}")

import sqlite3
import datetime

def save_kvs_data(path, data):
    json_string = json.dumps(data, indent=4)

    with open(path, "w") as file:
        file.write(json_string)

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

def save_first_kvs_data():
    save_kvs_data(first_kvs_file_path, first_kvs_data)

def save_second_kvs_data():
    save_kvs_data(second_kvs_file_path, second_kvs_data)
