# Created: 2024-04-15
# A simple module to backup strings, file contents, etc.

import base64
import enum
import os
import sqlite3
import typing

import pyddle_datetime as pdatetime

# Lazy loading:
__backup_file_path: str | None = None

def get_backup_file_path():
    global __backup_file_path # pylint: disable = global-statement

    if not __backup_file_path:
        # https://docs.python.org/3/library/os.path.html#os.path.expanduser
        __backup_file_path = os.path.join(os.path.expanduser("~"), ".pyddle_backup.json")

    return __backup_file_path

class ValueType(enum.Enum):
    STR = 1
    JSON_STR = 2
    BYTES = 3

def backup(key: str, value_type: ValueType, value: str | bytes, quiet: bool = True):
    try:
        with sqlite3.connect(get_backup_file_path()) as connection:
            cursor = connection.cursor()

            cursor.execute(
                "CREATE TABLE IF NOT EXISTS pyddle_backup ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "utc DATETIME NOT NULL, "
                    "key TEXT NOT NULL, "
                    "value_type INTEGER NOT NULL, "
                    "value TEXT NOT NULL)")

            utc_str = pdatetime.get_utc_now().isoformat()

            if value_type == ValueType.STR or value_type == ValueType.JSON_STR:
                if not isinstance(value, str):
                    raise RuntimeError("Value must be a string.")

                cursor.execute("INSERT INTO pyddle_backup (utc, key, value_type, value) VALUES (?, ?, ?, ?)", (utc_str, key, value_type.value, value))

            elif value_type == ValueType.BYTES:
                if not isinstance(value, bytes):
                    raise RuntimeError("Value must be bytes.")

                base64_str = base64.b64encode(typing.cast(bytes, value)).decode("ascii")

                cursor.execute("INSERT INTO pyddle_backup (utc, key, value_type, value) VALUES (?, ?, ?, ?)", (utc_str, key, value_type.value, base64_str))

            else:
                raise RuntimeError(f"Unsupported value type: {value_type}") # Re-raised only if not quiet.

            connection.commit()

    except Exception: # pylint: disable = broad-except
        if not quiet:
            raise
