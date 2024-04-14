# Created: 2024-03-07
# This script contains the possibly simplest logging mechanism that should be just enough for a small, single-threaded app.

import datetime
import os

import pyddle_datetime as pdatetime
import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_path as ppath
import pyddle_string as pstring

# Requires the developer to call pyddle_global.set_main_script_file_path() before using this module.
# I think it's OK; it's quick, runs at negligible cost and certainly improves the usability of the log file.

# Lazy loading:
__logs_directory_path: str | None = None # pylint: disable = invalid-name

def get_logs_directory_path():
    global __logs_directory_path # pylint: disable = global-statement

    if not __logs_directory_path:
        __logs_directory_path = os.path.join(ppath.dirname(pglobal.get_main_script_file_path()), "logs")

    return __logs_directory_path

# Hyphens, rather than underscores, are used to separate the elements following Google's recommendation.
# https://developers.google.com/search/docs/crawling-indexing/url-structure

# In Python, I consider script file names are also module names and the underscores in them are no more special than alphabets and digits; they are NOT separators.
# The following file name format is reasonable as the script file name may not contain hyphens while file name elements should be separated by hyphens.

# Lazy loading:
__log_file_path: str | None = None # pylint: disable = invalid-name

def get_log_file_path():
    global __log_file_path # pylint: disable = global-statement

    if not __log_file_path:
        utc_timestamp = pdatetime.utc_to_roundtrip_file_name_string(datetime.datetime.now(datetime.UTC))
        file_name_without_extension, _ = os.path.splitext(ppath.basename(pglobal.get_main_script_file_path()))
        __log_file_path = os.path.join(get_logs_directory_path(), f"log-{utc_timestamp}-{file_name_without_extension}.log")

    return __log_file_path

pending_logs: list[str] = []

def log(str_: str, indents = "", end = "\n", flush_ = False):
    if str_:
        pending_logs.append(f"{indents}{str_}{end}")

    else:
        pending_logs.append(end)

    if flush_:
        flush()

def log_lines(str_: list[str], indents = "", trailing = "", end = "\n", flush_ = False):
    if str_:
        for line in str_:
            parts = pstring.split_line_into_parts(line)

            if parts[1]:
                # Using the original string of the line.
                pending_logs.append(f"{indents}{line}{trailing}{end}")

            else:
                pending_logs.append(end)

    if flush_:
        flush()

def flush():
    if pending_logs:
        os.makedirs(get_logs_directory_path(), exist_ok = True)

        with pfs.open_file_and_write_utf_encoding_bom(get_log_file_path(), append = True) as file:
            for log_ in pending_logs:
                file.write(log_)

        pending_logs.clear()
