# Created: 2024-03-05
# This script contains string-related functions.

leveledIndents = [
    "",
    "    ",
    "        ",
    "            ",
    "                ",
    "                    ",
    "                        ",
    "                            ",
    "                                ",
    "                                    " # Index: 9
] # Length: 10

def to_visible_str(str):
    if str == None:
        return "(None)"

    if str == "":
        return "(Empty)"

    return str

# ------------------------------------------------------------------------------
#     Equality
# ------------------------------------------------------------------------------

# A sugar coating method to reduce writing "==" in code.
# Sometimes, we need to check the case-sensitivity of string comparisons.

def equals(str1, str2):
    return str1 == str2

def equals_ignore_case(str1, str2):
    if str1:
        if str2:
            return str1.lower() == str2.lower()

        else:
            return False

    else:
        if str2:
            return False

        else:
            return True

def equals_casefold(str1, str2):
    if str1:
        if str2:
            return str1.casefold() == str2.casefold()

        else:
            return False

    else:
        if str2:
            return False

        else:
            return True

def contains(str_array, str):
    for item in str_array:
        if equals(item, str):
            return True

    return False

def contains_ignore_case(str_array, str):
    for item in str_array:
        if equals_ignore_case(item, str):
            return True

    return False

def contains_casefold(str_array, str):
    for item in str_array:
        if equals_casefold(item, str):
            return True

    return False

# ------------------------------------------------------------------------------
#     Partial equality
# ------------------------------------------------------------------------------

def startswith(str, prefix):
    return str.startswith(prefix)

def startswith_ignore_case(str, prefix):
    return str.lower().startswith(prefix.lower())

def startswith_casefold(str, prefix):
    return str.casefold().startswith(prefix.casefold())

def equals_at(str, index, substring):
    str_length = len(str)
    substring_length = len(substring)

    # "".startswith("") returns True.
    # This is technically equals_at("", 0, "").

    # For us, a week for example does NOT start with an non-existent day,
    #     but in programming, the validity of the index of a substring may depend on its length.

    # Always an error.
    if index < 0:
        raise RuntimeError("Index out of range.")

    # Comparison occurs.
    if substring_length > 0:
        # Cant compare from the 8th day of a week.
        if index >= str_length:
            raise RuntimeError("Index out of range.")

    # It's more about technicality here.
    else:
        # Must work like "".startswith("") => True.
        if index > str_length:
            raise RuntimeError("Index out of range.")

        # If the substring is "" and the index is OK,
        #     the rest of the code can be skipped.
        return True

    # It's an option to check if index < 0 OR index >= str_length and, before that,
    #     return True if substring_length == 0 AND index == 0 considering it a special case.
    # But technically speaking, it's more about whether comparison occurs or not.
    # If it doesnt, the zero-length substring MAY stand at the very edge of the cliff unless it falls off.

    if index + substring_length > len(str):
        return False

    return str[index : index + substring_length] == substring

def equals_at_ignore_case(str, index, substring):
    str_length = len(str)
    substring_length = len(substring)

    if index < 0:
        raise RuntimeError("Index out of range.")

    if substring_length > 0:
        if index >= str_length:
            raise RuntimeError("Index out of range.")

    else:
        if index > str_length:
            raise RuntimeError("Index out of range.")

        return True

    if index + substring_length > len(str):
        return False

    return str[index : index + substring_length].lower() == substring.lower()

def equals_at_casefold(str, index, substring):
    str_length = len(str)
    substring_length = len(substring)

    if index < 0:
        raise RuntimeError("Index out of range.")

    if substring_length > 0:
        if index >= str_length:
            raise RuntimeError("Index out of range.")

    else:
        if index > str_length:
            raise RuntimeError("Index out of range.")

        return True

    if index + substring_length > len(str):
        return False

    return str[index : index + substring_length].casefold() == substring.casefold()

def endswith(str, suffix):
    return str.endswith(suffix)

def endswith_ignore_case(str, suffix):
    return str.lower().endswith(suffix.lower())

def endswith_casefold(str, suffix):
    return str.casefold().endswith(suffix.casefold())

# ------------------------------------------------------------------------------
#     Searching
# ------------------------------------------------------------------------------

def index_of(str, substring):
    return str.find(substring)

def index_of_ignore_case(str, substring):
    return str.lower().find(substring.lower())

def index_of_casefold(str, substring):
    return str.casefold().find(substring.casefold())

def index_of_any(str, substrings):
    # Checking for None, not caching.
    str_length = len(str)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        # Without this block, the next "for" loop will miss the case where one or more of the substrings are ""
        #     and the edge-of-cliff zero-comparison situation described in pyddle_string.py occurs.
        # This is a search-forward function; only the minimum index must be considered in edge cases.
        if substring == "":
            return 0

    # From now on, no zero-comparison will occur.
    # We can assume we are looking for something that exists.

    for index in range(str_length):
        for substring in substrings:
            if equals_at(str, index, substring):
                return index

    return -1

def index_of_any_ignore_case(str, substrings):
    str_length = len(str)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        if substring == "":
            return 0

    for index in range(str_length):
        for substring in substrings:
            if equals_at_ignore_case(str, index, substring):
                return index

    return -1

def index_of_any_casefold(str, substrings):
    str_length = len(str)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        if substring == "":
            return 0

    for index in range(str_length):
        for substring in substrings:
            if equals_at_casefold(str, index, substring):
                return index

    return -1

def last_index_of(str, substring):
    return str.rfind(substring)

def last_index_of_ignore_case(str, substring):
    return str.lower().rfind(substring.lower())

def last_index_of_casefold(str, substring):
    return str.casefold().rfind(substring.casefold())

def last_index_of_any(str, substrings):
    str_length = len(str)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        if substring == "":
            # Not str_length - 1.
            # "a".rfind("") returns 1.
            return str_length

    for index in range(str_length - 1, -1, -1):
        for substring in substrings:
            if equals_at(str, index, substring):
                return index

    return -1

def last_index_of_any_ignore_case(str, substrings):
    str_length = len(str)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        if substring == "":
            return str_length

    for index in range(str_length - 1, -1, -1):
        for substring in substrings:
            if equals_at_ignore_case(str, index, substring):
                return index

    return -1

def last_index_of_any_casefold(str, substrings):
    str_length = len(str)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        if substring == "":
            return str_length

    for index in range(str_length - 1, -1, -1):
        for substring in substrings:
            if equals_at_casefold(str, index, substring):
                return index

    return -1
