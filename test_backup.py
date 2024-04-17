# Created: 2024-04-15
# Tests pyddle_backup.py.

import datetime
import json
import sqlite3

import pyddle_backup as pbackup
import pyddle_console as pconsole
import pyddle_datetime as pdatetime
import pyddle_debugging as pdebugging
import pyddle_string as pstring
import pyddle_type as ptype

utc_now = pdatetime.get_utc_now()

days_ago = [utc_now - datetime.timedelta(days = days) for days in range(3)]

# The following literals are by GitHut Copilot:

keys = ["test_key", "Test_Key", "TEST_KEY"]

str_ = "Hello, world!" # pylint: disable = invalid-name

data = {
    "name": "John Doe",
    "age": 30,
    "city": "New York",
    "is_student": False,
    "courses": ["Math", "Science", "History"],
    "grades": {"Math": 90, "Science": 80, "History": 70}
}

json_str = json.dumps(data, indent = 4)

str_for_bytes = "Hello, bytes!" # pylint: disable = invalid-name
str_bytes = str_for_bytes.encode("ascii") # pylint: disable = invalid-name

values: dict[pbackup.ValueType, str | bytes] = {
    pbackup.ValueType.STR: str_,
    pbackup.ValueType.JSON_STR: json_str,
    pbackup.ValueType.BYTES: str_bytes
}

def delete_relevant_rows():
    with sqlite3.connect(pbackup.get_backup_file_path()) as connection:
        cursor = connection.cursor()

        cursor.execute("DELETE FROM pyddle_backup WHERE key IN (?, ?, ?)", keys)

        connection.commit()

        cursor.close()

delete_relevant_rows()

for days_ago_item in days_ago:
    for key in keys:
        for value_type, value in values.items():
            pbackup.backup(
                key = key,
                value_type = value_type,
                value = value,
                utc = days_ago_item,
                quiet = False) # Not quiet.

def restore_and_print(
    min_utc: datetime.datetime | None = None,
    max_utc: datetime.datetime | None = None,
    key_: str | None = None,
    key_ignore_case: bool = False,
    value_type_: pbackup.ValueType | None = None):

    data_ = pbackup.restore(
        min_utc = min_utc,
        max_utc = max_utc,
        key = key_,
        key_ignore_case = key_ignore_case,
        value_type = value_type_)

    argument_lines = []

    if min_utc:
        argument_lines.append(f"min_utc: {min_utc.date()}")

    if max_utc:
        argument_lines.append(f"max_utc: {max_utc.date()}")

    if key_:
        argument_lines.append(f"key: {key_}")
        argument_lines.append(f"key_ignore_case: {key_ignore_case}")

    if value_type_:
        argument_lines.append(f"value_type: {value_type_.name}")

    if argument_lines:
        pconsole.print("Arguments:")
        pconsole.print_lines(argument_lines, indents = pstring.LEVELED_INDENTS[1])

    else:
        pconsole.print("No arguments.")

    data_lines = []

    for row in data_:
        line_parts = []

        line_parts.append(f"id: {row['id']}")
        line_parts.append(f"utc: {datetime.datetime.fromisoformat(row['utc']).date()}")
        line_parts.append(f"key: {row['key']}")
        line_parts.append(f"value_type: {ptype.str_to_enum_by_int_value(row['value_type'], pbackup.ValueType).name}")
        # We wont bother with "value".
        # Each is just a string or a string representation of bytes.

        data_lines.append(", ".join(line_parts))

    if data_lines:
        pconsole.print("Data:")
        pconsole.print_lines(data_lines, indents = pstring.LEVELED_INDENTS[1])

    else:
        pconsole.print("No data.")

# Results available in: BU44 Results of test_backup.py.json

restore_and_print()

# We have 3 days of data.
restore_and_print(min_utc = days_ago[1]) # Inclusively => 0, 1 days ago.
restore_and_print(max_utc = days_ago[0]) # Exclusively => 1, 2 days ago.

restore_and_print(key_ = keys[1], key_ignore_case = False)
restore_and_print(key_ = keys[1], key_ignore_case = True)
restore_and_print(value_type_ = pbackup.ValueType.JSON_STR)

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
