# Created: 2024-03-07
# This script contains utility functions for console output.

from builtins import print as builtin_print
import colorama

# Specified colors appear differently depending on the platform.
# These should be an acceptable starting point.

# Sugar coating.
# We may be adding some shared functionalities to all print-related functions in the future.
def print(str, end="\n"):
    builtin_print(str, end=end)

def print_important(str, end="\n"):
    builtin_print(f"{colorama.Back.BLUE}{colorama.Fore.WHITE}{str}{colorama.Style.RESET_ALL}", end=end)

def print_warning(str, end="\n"):
    builtin_print(f"{colorama.Back.YELLOW}{colorama.Fore.BLACK}{str}{colorama.Style.RESET_ALL}", end=end)

def print_error(str, end="\n"):
    builtin_print(f"{colorama.Back.RED}{colorama.Fore.WHITE}{str}{colorama.Style.RESET_ALL}", end=end)
