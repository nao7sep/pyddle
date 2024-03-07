# Created: 2024-03-07
# This script aims to provide an unified way to output strings to the console and a log file.

import pyddle_console as console
import pyddle_logging as logging

def print_and_log(str, end="\n", flush=False):
    console.print(str, end=end)
    logging.log(str, end=end, flush=flush)

def print_and_log_important(str, end="\n", flush=False):
    console.print_important(str, end=end)
    logging.log(str, end=end, flush=flush)

def print_and_log_warning(str, end="\n", flush=False):
    console.print_warning(str, end=end)
    logging.log(str, end=end, flush=flush)

def print_and_log_error(str, end="\n", flush=False):
    console.print_error(str, end=end)
    logging.log(str, end=end, flush=flush)
