# Created: 2024-03-07
# This script contains utility functions for console output.

from builtins import print as builtin_print
import colorama

# Specified colors appear differently depending on the platform.
# These should be an acceptable starting point.

# Sugar coating.
# We may be adding some shared functionalities to all print-related functions in the future.
def print(str, indents="", end="\n"):
    builtin_print(f"{indents}{str}", end=end)

def print_important(str, indents="", end="\n"):
    builtin_print(f"{indents}{colorama.Back.BLUE}{colorama.Fore.WHITE}{str}{colorama.Style.RESET_ALL}", end=end) # The indentation is not colored.

def print_warning(str, indents="", end="\n"):
    builtin_print(f"{indents}{colorama.Back.YELLOW}{colorama.Fore.BLACK}{str}{colorama.Style.RESET_ALL}", end=end)

def print_error(str, indents="", end="\n"):
    builtin_print(f"{indents}{colorama.Back.RED}{colorama.Fore.WHITE}{str}{colorama.Style.RESET_ALL}", end=end)
