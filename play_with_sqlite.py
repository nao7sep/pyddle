# Created: 2024-03-04
# This script plays with SQLite for educational purposes.

import datetime
import sqlite3

import pyddle_debugging as pdebugging
import pyddle_string as pstring

# https://www.sqlite.org/inmemorydb.html
connection = sqlite3.connect(":memory:")

cursor = connection.cursor()

# Looking for a good way to store datetime values in SQLite:

cursor.execute("DROP TABLE IF EXISTS table1")

cursor.execute(
    "CREATE TABLE IF NOT EXISTS table1 ("
        "now_in_utc DATETIME NOT NULL, "
        "utc_string DATETIME NOT NULL, "
        "utc_string_as_utc DATETIME NOT NULL, "
        "utc_string_as_localtime DATETIME NOT NULL, "
        "now_in_localtime DATETIME NOT NULL, "
        "localtime_string DATETIME NOT NULL, "
        "localtime_string_as_utc DATETIME NOT NULL, "
        "localtime_string_as_localtime DATETIME NOT NULL)")

utc_string = datetime.datetime.now(datetime.UTC).isoformat()
print(f"utc_string: {utc_string}")

localtime_string = datetime.datetime.now().isoformat()
print(f"localtime_string: {localtime_string}")

cursor.execute(
    "INSERT INTO table1 ("
        "now_in_utc, "
        "utc_string, "
        "utc_string_as_utc, "
        "utc_string_as_localtime, "
        "now_in_localtime, "
        "localtime_string, "
        "localtime_string_as_utc, "
        "localtime_string_as_localtime) "
    "VALUES ("
        "DATETIME('now', 'utc'), "
        "?, "
        "DATETIME(?, 'utc'), "
        "DATETIME(?, 'localtime'), "
        "DATETIME('now', 'localtime'), "
        "?, "
        "DATETIME(?, 'utc'), "
        "DATETIME(?, 'localtime'))",
    (utc_string, utc_string, utc_string, localtime_string, localtime_string, localtime_string))

cursor.execute("SELECT * FROM table1")

data = cursor.fetchall()

print("Data from table1:")

# https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.description
column_names = [description[0] for description in cursor.description]

for row in data: # Expecting only one row.
    # https://docs.python.org/3/library/functions.html#zip
    for column_name, value in zip(column_names, row):
        print(f"{pstring.LEVELED_INDENTS[1]}{column_name}: {value}")

cursor.execute(f"SELECT COUNT(*) FROM table1 WHERE strftime('%Y', utc_string) = '{datetime.datetime.now(datetime.UTC).year}'")

data = cursor.fetchall()

if data[0][0]: # Assuming one row with one column is returned.
    print("There's a row in table1 with a datetime value from the current year.")

else:
    print("There's no row in table1 with a datetime value from the current year.")

connection.close()

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
