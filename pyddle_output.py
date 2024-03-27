# Created: 2024-03-07
# This script aims to provide an unified way to output strings to the console and a log file.

import pyddle_console as console
import pyddle_logging as logging

def print_and_log(str, indents="", end="\n", flush=False):
    if not str:
        indents = ""

    console.print(str, indents=indents, end=end)
    logging.log(str, indents=indents, end=end, flush=flush)

def print_and_log_important(str, indents="", end="\n", flush=False):
    if not str:
        indents = ""

    console.print_important(str, indents=indents, end=end)
    logging.log(str, indents=indents, end=end, flush=flush)

def print_and_log_warning(str, indents="", end="\n", flush=False):
    if not str:
        indents = ""

    console.print_warning(str, indents=indents, end=end)
    logging.log(str, indents=indents, end=end, flush=flush)

def print_and_log_error(str, indents="", end="\n", flush=False):
    if not str:
        indents = ""

    console.print_error(str, indents=indents, end=end)
    logging.log(str, indents=indents, end=end, flush=flush)
