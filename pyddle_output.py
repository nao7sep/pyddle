# Created: 2024-03-07
# This script aims to provide an unified way to output strings to the console and a log file.

import pyddle_console as console
import pyddle_logging as logging

def print_and_log(str, multiline=False, indents="", end="\n", flush=False):
    console.print(str, multiline=multiline, indents=indents, end=end)
    logging.log(str, multiline=multiline, indents=indents, end=end, flush=flush)

def print_and_log_important(str, multiline=False, indents="", end="\n", flush=False):
    console.print_important(str, multiline=multiline, indents=indents, end=end)
    logging.log(str, multiline=multiline, indents=indents, end=end, flush=flush)

def print_and_log_warning(str, multiline=False, indents="", end="\n", flush=False):
    console.print_warning(str, multiline=multiline, indents=indents, end=end)
    logging.log(str, multiline=multiline, indents=indents, end=end, flush=flush)

def print_and_log_error(str, multiline=False, indents="", end="\n", flush=False):
    console.print_error(str, multiline=multiline, indents=indents, end=end)
    logging.log(str, multiline=multiline, indents=indents, end=end, flush=flush)
