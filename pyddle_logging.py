# Created: 2024-03-07
# This script contains the possibly simplest logging mechanism that should be just enough for a small, single-threaded app.

import pyddle_first as first
first.set_main_script_file_path(__file__)

import datetime
import os
import pyddle_datetime
import pyddle_file_system as file_system
import pyddle_path # path is a too common name.

logs_directory_path = os.path.join(pyddle_path.dirname(__file__), "logs")

# Requires the developer to call pyddle_first.set_main_script_file_path() before using this module.
# I think it's OK; it's quick, runs at negligible cost and certainly improves the usability of the log file.

# Hyphens, rather than underscores, are used to separate the elements following Google's recommendation.
# https://developers.google.com/search/docs/crawling-indexing/url-structure

# In Python, I consider script file names are also module names and the underscores in them are no more special than alphabets and digits; they are NOT separators.
# The following file name format is reasonable as the script file name may not contain hyphens while file name elements should be separated by hyphens.

log_file_path = os.path.join(logs_directory_path, f"log-{pyddle_datetime.utc_to_roundtrip_file_name_string(datetime.datetime.now(datetime.UTC))}-{first.get_main_script_file_name_without_extension()}.log")

logs = []

def log(str, indents="", end="\n", flush=False):
    if not str:
        indents = ""

    logs.append(f"{indents}{str}{end}")

    if flush:
        flush()

def flush():
    if logs:
        os.makedirs(logs_directory_path, exist_ok=True)

        with file_system.open_file_and_write_utf_encoding_bom(log_file_path, append=True) as file:
            for log in logs:
                file.write(log)

        logs.clear()
