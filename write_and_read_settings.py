﻿# Created: 2024-02-21
# This script demonstrates how to write and read settings in various file formats.

import base64
import configparser
import csv
import json
import sqlite3
import typing
import xml.dom.minidom
import xml.etree.ElementTree

import pyddle_debugging as pdebugging
import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

# Initialize variables of frequently used types.

INT_VAR = 1
FLOAT_VAR = 1.1
STR_VAR = "Hello"
LIST_VAR = [1, "2_2", 3]
TUPLE_VAR = ("4_4", 5)
BOOL_VAR = True
BYTES_VAR = "はろ～".encode("UTF-8") # A friendly representation of "Hello" in Japanese.
NONE_VAR: None = None

# Initialize a dictionary with the variables.

data = {
    "int": INT_VAR,
    "float": FLOAT_VAR,
    "str": STR_VAR,
    "list": LIST_VAR,
    "tuple": TUPLE_VAR,
    "bool": BOOL_VAR,
    "bytes": BYTES_VAR,
    "none": NONE_VAR
}

# Create the "output" subdirectory and set the working directory to it.

pfs.make_and_move_to_output_subdirectory()

# ------------------------------------------------------------------------------
#     INI file
# ------------------------------------------------------------------------------

# Write the data into a INI file.

config = configparser.ConfigParser()
config.add_section("data")

for key, value in data.items():
    config["data"][key] = str(value)

with pfs.open_file_and_write_utf_encoding_bom("write_and_read_settings.ini") as config_file:
    config.write(config_file)

# Read the data from the INI file.

config.clear()

with pfs.open_file_and_detect_utf_encoding("write_and_read_settings.ini") as config_file:
    config.read_file(config_file)

print("Data from the INI file:")

for key, value in config["data"].items():
    print(f"{pstring.LEVELED_INDENTS[1]}{key}: {value}")

# ------------------------------------------------------------------------------
#     JSON file
# ------------------------------------------------------------------------------

# Convert the bytes in the data to a Base64 string for JSON serialization.

data["bytes"] = base64.b64encode(typing.cast(bytes, data["bytes"])).decode("ascii")

print(f"Bytes converted to Base64: {data['bytes']}")

# Write the data into a JSON file.

with pfs.open_file_and_write_utf_encoding_bom("write_and_read_settings.json") as json_file:
    json.dump(data, json_file, indent = 4)

# Read the data from the JSON file.

with pfs.open_file_and_detect_utf_encoding("write_and_read_settings.json") as json_file:
    data_from_json = json.load(json_file)

# Convert the Base64 strings in the 2 portions of data back to bytes.

data["bytes"] = base64.b64decode(typing.cast(str, data["bytes"]))
data_from_json["bytes"] = base64.b64decode(data_from_json["bytes"])

print("Data from the JSON file:")

for key, value in data_from_json.items():
    print(f"{pstring.LEVELED_INDENTS[1]}{key}: {value}")

# ------------------------------------------------------------------------------
#     XML file
# ------------------------------------------------------------------------------

# Write the data into a XML file.

root = xml.etree.ElementTree.Element("data")

for key, value in data.items():
    xml.etree.ElementTree.SubElement(root, key).text = str(value)

# Convert to pretty XML.

pretty_xml = xml.dom.minidom.parseString (xml.etree.ElementTree.tostring(root, 'UTF-8')).toprettyxml(indent = pstring.LEVELED_INDENTS[1])

with pfs.open_file_and_write_utf_encoding_bom("write_and_read_settings.xml") as xml_file:
    xml_file.write(pretty_xml)

# Read the data from the XML file.

with pfs.open_file_and_detect_utf_encoding("write_and_read_settings.xml") as xml_file:
    tree = xml.etree.ElementTree.parse(xml_file)

root = tree.getroot()

print("Data from the XML file:")

for child in root:
    print(f"{pstring.LEVELED_INDENTS[1]}{child.tag}: {child.text}")

# ------------------------------------------------------------------------------
#     CSV file
# ------------------------------------------------------------------------------

# Write the data into a CSV file.

with pfs.open_file_and_write_utf_encoding_bom("write_and_read_settings.csv") as csv_file:
    # "\r\n", the default value on Windows, might cause the parser to read an empty row within each line ending.
    writer = csv.writer(csv_file, lineterminator = "\n")

    for key, value in data.items():
        writer.writerow([key, value])

# Read the data from the CSV file.

# The value for the none key will be read as an empty string as the CSV format doesnt support None values.

with pfs.open_file_and_detect_utf_encoding("write_and_read_settings.csv") as csv_file:
    reader = csv.reader(csv_file)
    data_from_csv = list(reader)

print("Data from the CSV file:")

for row in data_from_csv:
    print(f"{pstring.LEVELED_INDENTS[1]}{row[0]}: {row[1]}")

# ------------------------------------------------------------------------------
#     SQLite database
# ------------------------------------------------------------------------------

# Write the data into a SQLite database.

conn = sqlite3.connect("write_and_read_settings.db")

c = conn.cursor()

# The table is created if it doesnt exist, and it has a column for how many times each row has been updated, and all the columns are not nullable.

c.execute(
    "CREATE TABLE IF NOT EXISTS data ("
        "key TEXT PRIMARY KEY NOT NULL, "
        "value TEXT NOT NULL, "
        "update_count INTEGER NOT NULL)")

for key, value in data.items():
    # If a row with the same key doesnt exist, the SELECT statement will return NULL, which will then be coalesced to 1.
    c.execute(
        "INSERT OR REPLACE INTO data (key, value, update_count) "
        "VALUES (?, ?, COALESCE ((SELECT update_count + 1 FROM data WHERE key = ?), 1))",
        (key, str(value), key))

conn.commit()
conn.close()

# Read the data from the SQLite database.

conn = sqlite3.connect("write_and_read_settings.db")

c = conn.cursor()

c.execute("SELECT * FROM data")

data_from_sqlite = c.fetchall()

conn.close()

print("Data from the SQLite database:")

for row in data_from_sqlite:
    print(f"{pstring.LEVELED_INDENTS[1]}{row[0]}: {row[1]}")

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
