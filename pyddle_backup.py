# Created: 2024-04-15
# A simple module to backup strings, file contents, etc.

import base64
import datetime
import enum
import os
import sqlite3
import typing

import pyddle_datetime as pdatetime
import pyddle_errors as perrors

# Lazy loading:
__backup_file_path: str | None = None

def get_backup_file_path():
    global __backup_file_path # pylint: disable = global-statement

    if not __backup_file_path:
        # https://docs.python.org/3/library/os.path.html#os.path.expanduser
        __backup_file_path = os.path.join(os.path.expanduser("~"), ".pyddle_backup.db")

    return __backup_file_path

class ValueType(enum.Enum):
    STR = 1
    JSON_STR = 2
    BYTES = 3

def backup(
    key: str,
    value_type: ValueType,
    value: str | bytes,
    utc: datetime.datetime | None = None,
    quiet: bool = True):

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

            utc_str = (utc or pdatetime.get_utc_now()).isoformat()

            if value_type == ValueType.STR or value_type == ValueType.JSON_STR:
                if not isinstance(value, str):
                    raise perrors.FormatError("Value must be a string.")

                cursor.execute(
                    "INSERT INTO pyddle_backup (utc, key, value_type, value) "
                    "VALUES (?, ?, ?, ?)",
                    (utc_str, key, value_type.value, value))

            elif value_type == ValueType.BYTES:
                if not isinstance(value, bytes):
                    raise perrors.FormatError("Value must be bytes.")

                base64_str = base64.b64encode(typing.cast(bytes, value)).decode("ascii")

                cursor.execute(
                    "INSERT INTO pyddle_backup (utc, key, value_type, value) "
                    "VALUES (?, ?, ?, ?)",
                    (utc_str, key, value_type.value, base64_str))

            else:
                raise perrors.NotSupportedError(f"Unsupported value type: {value_type}") # Re-raised only if not quiet.

            connection.commit()

            cursor.close()

    except Exception: # pylint: disable = broad-except
        if not quiet:
            raise

def restore(min_utc: datetime.datetime | None = None,
            max_utc: datetime.datetime | None = None,
            key: str | None = None,
            key_ignore_case: bool = False,
            value_type: ValueType | None = None):

    ''' "min_utc" is inclusive. "max_utc" is exclusive. Unlike "backup", this method raises exceptions. '''

    with sqlite3.connect(get_backup_file_path()) as connection:
        connection.row_factory = sqlite3.Row # Enables column access by name: row["column_name"]
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM sqlite_master WHERE type = 'table' AND name = 'pyddle_backup'")

        if not cursor.fetchone():
            return []

        where_clause_lines = []
        parameter_values: list[str | int] = []

        if min_utc:
            where_clause_lines.append("utc >= ?")
            parameter_values.append(min_utc.isoformat())

        if max_utc:
            where_clause_lines.append("utc < ?")
            parameter_values.append(max_utc.isoformat())

        if key:
            if key_ignore_case:
                where_clause_lines.append("LOWER(key) = LOWER(?)")

            else:
                where_clause_lines.append("key = ?")

            parameter_values.append(key)

        if value_type:
            where_clause_lines.append("value_type = ?")
            parameter_values.append(value_type.value)

        if where_clause_lines:
            where_clause = " AND ".join(where_clause_lines)
            query = f"SELECT * FROM pyddle_backup WHERE {where_clause}"
            cursor.execute(query, parameter_values)

        else:
            query = "SELECT * FROM pyddle_backup"
            cursor.execute(query)

        # "cursor" should be closed by the context manager of the connection.
        return cursor.fetchall()
