# Created: 2024-03-07
# This script contains the possibly simplest logging mechanism that should be just enough for a small, single-threaded app.

import datetime
import os

import pyddle_datetime
import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_path as ppath
import pyddle_string as pstring

# Requires the developer to call pyddle_first.set_main_script_file_path() before using this module.
# I think it's OK; it's quick, runs at negligible cost and certainly improves the usability of the log file.

logs_directory_path = os.path.join(ppath.dirname(pglobal.get_main_script_file_path()), "logs")

# Hyphens, rather than underscores, are used to separate the elements following Google's recommendation.
# https://developers.google.com/search/docs/crawling-indexing/url-structure

# In Python, I consider script file names are also module names and the underscores in them are no more special than alphabets and digits; they are NOT separators.
# The following file name format is reasonable as the script file name may not contain hyphens while file name elements should be separated by hyphens.

log_file_path = os.path.join(logs_directory_path, f"log-{pyddle_datetime.utc_to_roundtrip_file_name_string(datetime.datetime.now(datetime.UTC))}-{ppath.basename(pglobal.get_main_script_file_path())}.log")

logs = []

def log(_str, indents="", end="\n", _flush=False):
    if _str:
        logs.append(f"{indents}{_str}{end}")

    else:
        logs.append(end)

    if _flush:
        _flush()

def log_lines(_str: list[str], indents="", trailing="", end="\n", _flush=False):
    if _str:
        for line in _str:
            parts = pstring.split_line_into_parts(line)

            if parts[1]:
                # Using the original string of the line.
                logs.append(f"{indents}{line}{trailing}{end}")

            else:
                logs.append(end)

    if _flush:
        _flush()

def flush():
    if logs:
        os.makedirs(logs_directory_path, exist_ok=True)

        with pfs.open_file_and_write_utf_encoding_bom(log_file_path, append=True) as file:
            for _log in logs:
                file.write(_log)

        logs.clear()
