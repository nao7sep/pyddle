# Created: 2024-03-07
# This script aims to provide an unified way to output strings to the console and a log file.

import pyddle_console as console
import pyddle_logging as logging

# These methods assume "str" is a raw string, meaning it has to be output as-is.
# If "str" is falsy, "indents" wont be output, but "end" will be.
# "indents" and "end" will never be colored.

def print_and_log(str, indents="", colors="", end="\n", flush=False):
    console.print(str, indents=indents, colors=colors, end=end)
    logging.log(str, indents=indents, end=end, flush=flush)

# Each line will be split into 1) Indents, 2) Visible content, 3) Trailing whitespace.

# The default value of "colors" is None, rather than [], to indicate that the coloring can be disabled.

# Only the visible content of #2 will be colored.

# Unlike print_and_log, "trailing" is supported.
# Its value will be joined with #3 of the input string.
# This is merely formality; if #1 and #3 are extracted and #1 is joined with "indents", #3 alone cant be discarded.

# If #2 is falsy, "indents", the indentation and trailing whitespace parts of #2 and "trailing" wont be output, but "end" will be.

def print_and_log_lines(str: list[str], indents="", colors: list[str]=None, trailing="", end="\n", flush=False):
    console.print_lines(str, indents=indents, colors=colors, trailing=trailing, end=end)
    logging.log_lines(str, indents=indents, trailing=trailing, end=end, flush=flush)
