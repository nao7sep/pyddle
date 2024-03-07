# Created: 2024-03-07
# This script contains the possibly simplest logging mechanism that should be just enough for a small, single-threaded app.

import datetime
import os
import pyddle_datetime
import pyddle_file_system as file_system

logs_directory_path = os.path.join(os.path.dirname(__file__), "logs")
log_file_path = os.path.join(logs_directory_path, pyddle_datetime.utc_to_roundtrip_file_name_string(datetime.datetime.now(datetime.UTC)) + ".log")

logs = []

def log(str, end="\n", flush=False):
    logs.append(str + end)

    if flush:
        flush()

def flush():
    if logs:
        os.makedirs(logs_directory_path, exist_ok=True)

        with file_system.open_file_and_write_utf_encoding_bom(log_file_path, append=True) as file:
            for log in logs:
                file.write(log)

        logs.clear()
