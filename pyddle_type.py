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
    except Exception: # pylint: disable = broad-except
        return default

def str_to_float(str_):
    return float(str_)

def str_to_float_or_default(str_, default):
    try:
        return float(str_)
    except Exception: # pylint: disable = broad-except
        return default

def str_to_complex(str_):
    return complex(str_)

def str_to_complex_or_default(str_, default):
    try:
        return complex(str_)
    except Exception: # pylint: disable = broad-except
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
    except Exception: # pylint: disable = broad-except
        return default

# ------------------------------------------------------------------------------
#     String to Enum
# ------------------------------------------------------------------------------

# I think we should basically make enum item values integers for flexibility,
#     like we can use the names for readability OR the values for performance.
# Then, as the names would be all uppercase, when we use the names,
#     they should be converted to lowercase to be a little prettier.

# Sometimes, it's better to use strings as the values of an enum type.
# Like when strings containing symbols are required as arguments and they cant be used as names.
# Also, when the enum type is merely a collection of literal strings.

# The following methods will help us handle either case:

def str_to_enum_by_name(str_, enum_type, ignore_case = True):
    member = try_str_to_enum_by_name(str_, enum_type=enum_type, ignore_case=ignore_case)

    if member:
        return member

    raise RuntimeError(f"Invalid enum name: {str_}")

def try_str_to_enum_by_name(str_, enum_type, ignore_case = True):
    for member in enum_type:
        if ignore_case:
            if pstring.equals_ignore_case(member.name, str_):
                return member

        else:
            if member.name == str_:
                return member

    return None

def str_to_enum_by_str_value(str_, enum_type, ignore_case = True):
    member = try_str_to_enum_by_str_value(str_, enum_type=enum_type, ignore_case=ignore_case)

    if member:
        return member

    raise RuntimeError(f"Invalid enum value: {str_}")

def try_str_to_enum_by_str_value(str_, enum_type, ignore_case = True):
    for member in enum_type:
        if ignore_case:
            if pstring.equals_ignore_case(member.value, str_):
                return member

        else:
            if member.value == str_:
                return member

    return None

# I'm not sure if we need a pair of methods for each value type.
# It doesnt hurt to have them and we might implement some checks in the future,
#     like an exception is raised if the underlying types differ.

def str_to_enum_by_int_value(value, enum_type):
    member = try_str_to_enum_by_int_value(value, enum_type=enum_type)

    if member:
        return member

    raise RuntimeError(f"Invalid enum value: {value}")

def try_str_to_enum_by_int_value(value, enum_type):
    for member in enum_type:
        if member.value == value:
            return member

    return None

def str_to_enum_by_float_value(value, enum_type):
    member = try_str_to_enum_by_float_value(value, enum_type=enum_type)

    if member:
        return member

    raise RuntimeError(f"Invalid enum value: {value}")

def try_str_to_enum_by_float_value(value, enum_type):
    for member in enum_type:
        if member.value == value:
            return member

    return None

def str_to_enum_by_complex_value(value, enum_type):
    member = try_str_to_enum_by_complex_value(value, enum_type=enum_type)

    if member:
        return member

    raise RuntimeError(f"Invalid enum value: {value}")

def try_str_to_enum_by_complex_value(value, enum_type):
    for member in enum_type:
        if member.value == value:
            return member

    return None

def str_to_enum_by_bool_value(value, enum_type):
    member = try_str_to_enum_by_bool_value(value, enum_type=enum_type)

    if member:
        return member

    raise RuntimeError(f"Invalid enum value: {value}")

def try_str_to_enum_by_bool_value(value, enum_type):
    for member in enum_type:
        if member.value == value:
            return member

    return None
