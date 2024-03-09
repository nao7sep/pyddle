# Created: 2024-03-07
# This script aims to provide an unified way to output strings to the console and a log file.

import pyddle_console as console
import pyddle_logging as logging

def print_and_log(str, indent="", end="\n", flush=False):
    console.print(str, indent=indent, end=end)
    logging.log(str, indent=indent, end=end, flush=flush)

def print_and_log_important(str, indent="", end="\n", flush=False):
    console.print_important(str, indent=indent, end=end)
    logging.log(str, indent=indent, end=end, flush=flush)

def print_and_log_warning(str, indent="", end="\n", flush=False):
    console.print_warning(str, indent=indent, end=end)
    logging.log(str, indent=indent, end=end, flush=flush)

def print_and_log_error(str, indent="", end="\n", flush=False):
    console.print_error(str, indent=indent, end=end)
    logging.log(str, indent=indent, end=end, flush=flush)
