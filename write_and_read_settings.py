# Created: 2024-02-21
# This script demonstrates how to write and read settings in various file formats.

# Initialize variables of frequently used types.

_int = 1
_float = 1.1
_str = "Hello"
_list = [1, "2_2", 3]
_tuple = ("4_4", 5)
_bool = True
_bytes = "はろ～".encode("utf-8") # A friendly representation of "Hello" in Japanese.
_none = None

# Initialize a dictionary with the variables.

data = {
    "int": _int,
    "float": _float,
    "str": _str,
    "list": _list,
    "tuple": _tuple,
    "bool": _bool,
    "bytes": _bytes,
    "none": _none
}

# Create the "output" subdirectory and set the working directory to it.

import os

os.makedirs("output", exist_ok=True)
os.chdir("output")

# Write the data into a INI file.

import configparser

config = configparser.ConfigParser()
config.add_section("data")

for key, value in data.items():
    config["data"][key] = str(value)

with open("write_and_read_settings.ini", "w") as configfile:
    config.write(configfile)

# Read the data from the INI file.

config.clear()

config.read("write_and_read_settings.ini")

print("Data from the INI file:")

for key, value in config["data"].items():
    print(f"    {key}: {value}")

# Convert the bytes in the data to a Base64 string for JSON serialization.

import base64

data["bytes"] = base64.b64encode(data["bytes"]).decode("ascii")

print(f"Bytes converted to Base64: {data['bytes']}")

# Write the data into a JSON file.

import json

with open("write_and_read_settings.json", "w") as jsonfile:
    json.dump(data, jsonfile, indent=4)

# Read the data from the JSON file.

with open("write_and_read_settings.json", "r") as jsonfile:
    data_from_json = json.load(jsonfile)

# Convert the Base64 strings in the 2 portions of data back to bytes.

data["bytes"] = base64.b64decode(data["bytes"])
data_from_json["bytes"] = base64.b64decode(data_from_json["bytes"])

print("Data from the JSON file:")

for key, value in data_from_json.items():
    print(f"    {key}: {value}")

# Write the data into a XML file.

import xml.etree.ElementTree as ET

root = ET.Element("data")

for key, value in data.items():
    ET.SubElement(root, key).text = str(value)

# Convert to pretty XML.

import xml.dom.minidom

prettyXml = xml.dom.minidom.parseString (ET.tostring(root, 'utf-8')).toprettyxml(indent="    ")

with open("write_and_read_settings.xml", "w") as xmlfile:
    xmlfile.write(prettyXml)

# Read the data from the XML file.

tree = ET.parse("write_and_read_settings.xml")

root = tree.getroot()

print("Data from the XML file:")

for child in root:
    print(f"    {child.tag}: {child.text}")

# Write the data into a CSV file.

import csv

# The newline="" part specifies that line endings should not be altered.
# Without this, Python would automatically convert line endings depending on the platform, which could corrupt the file.

with open("write_and_read_settings.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)

    for key, value in data.items():
        writer.writerow([key, value])

# Read the data from the CSV file.

# The value for the none key will be read as an empty string as the CSV format doesnt support None values.

with open("write_and_read_settings.csv", "r", newline="") as csvfile:
    reader = csv.reader(csvfile)
    data_from_csv = list(reader)

print("Data from the CSV file:")

for row in data_from_csv:
    print(f"    {row[0]}: {row[1]}")

# Write the data into a SQLite database.

import sqlite3

conn = sqlite3.connect("write_and_read_settings.db")

c = conn.cursor()

# The table is created if it doesnt exist, and it has a column for how many times each row has been updated, and all the columns are not nullable.

c.execute("CREATE TABLE IF NOT EXISTS data (key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL, update_count INTEGER NOT NULL)")

for key, value in data.items():
    # If a row with the same key doesnt exist, the SELECT statement will return NULL, which will then be coalesced to 1.
    c.execute("INSERT OR REPLACE INTO data (key, value, update_count) VALUES (?, ?, COALESCE ((SELECT update_count + 1 FROM data WHERE key = ?), 1))", (key, str(value), key))

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
    print(f"    {row[0]}: {row[1]}")
