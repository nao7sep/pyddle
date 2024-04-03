# Created: 2024-03-23
# Type-conversion-related things.

import pyddle_string as pstring

# We dont necessarily have to use these just to parse strings.
# Some will be useful.
# The others exist because they dont have a reason not to
#     and I dont want to have to look for them when I attempt to write consistent code.

def str_to_int(str_):
    return int(str_)

def str_to_int_or_default(str_, default):
    try:
        return int(str_)
    except Exception: # pylint: disable=broad-except
        return default

def str_to_float(str_):
    return float(str_)

def str_to_float_or_default(str_, default):
    try:
        return float(str_)
    except Exception: # pylint: disable=broad-except
        return default

def str_to_complex(str_):
    return complex(str_)

def str_to_complex_or_default(str_, default):
    try:
        return complex(str_)
    except Exception: # pylint: disable=broad-except
        return default

# Properly capitalized string representations of boolean values.
# Then, string.contains_ignore_case compares the strings in a way that is not most efficient.

# There's a chance that I'll be adding more in languages other than English.
# I might also implement a method that parses a string and returns a boolean value together with its properly capitalized string representation.
# So, I'm starting with this slightly redundant approach.

TRUE_STRS = ["True", "Yes", "1"] # I wont be covering numbers other than 1 for now.
FALSE_STRS = ["False", "No", "0"]

def str_to_bool(str_):
    if pstring.contains_ignore_case(TRUE_STRS, str_):
        return True

    if pstring.contains_ignore_case(FALSE_STRS, str_):
        return False

    raise RuntimeError(f"Invalid boolean string: {str_}")

def str_to_bool_or_default(str_, default):
    try:
        return str_to_bool(str_)
    except Exception: # pylint: disable=broad-except
        return default
