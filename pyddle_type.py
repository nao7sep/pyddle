# Created: 2024-03-23
# Type-conversion-related things.

import pyddle_string as string

# We dont necessarily have to use these just to parse strings.
# Some will be useful.
# The others exist because they dont have a reason not to
#     and I dont want to have to look for them when I attempt to write consistent code.

def str_to_int(str):
    return int(str)

def str_to_int_or_default(str, default):
    try:
        return int(str)
    except Exception:
        return default

def str_to_float(str):
    return float(str)

def str_to_float_or_default(str, default):
    try:
        return float(str)
    except Exception:
        return default

def str_to_complex(str):
    return complex(str)

def str_to_complex_or_default(str, default):
    try:
        return complex(str)
    except Exception:
        return default

# Properly capitalized string representations of boolean values.
# Then, string.contains_ignore_case compares the strings in a way that is not most efficient.

# There's a chance that I'll be adding more in languages other than English.
# I might also implement a method that parses a string and returns a boolean value together with its properly capitalized string representation.
# So, I'm starting with this slightly redundant approach.

boolTrueStrs = ["True", "Yes", "1"] # I wont be covering numbers other than 1 for now.
boolFalseStrs = ["False", "No", "0"]

def str_to_bool(str):
    if string.contains_ignore_case(boolTrueStrs, str):
        return True

    if string.contains_ignore_case(boolFalseStrs, str):
        return False

    raise RuntimeError(f"Invalid boolean string: {str}")

def str_to_bool_or_default(str, default):
    try:
        return str_to_bool(str)
    except Exception:
        return default
