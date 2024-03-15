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
    substring_length = len(substring)

    if index + substring_length > len(str):
        return False

    return str[index : index + substring_length] == substring

def equals_at_ignore_case(str, index, substring):
    substring_length = len(substring)

    if index + substring_length > len(str):
        return False

    return str[index : index + substring_length].lower() == substring.lower()

def equals_at_casefold(str, index, substring):
    substring_length = len(substring)

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
    return str.index(substring)

def index_of_ignore_case(str, substring):
    return str.lower().find(substring.lower())

def index_of_casefold(str, substring):
    return str.casefold().find(substring.casefold())

def index_of_any(str, substrings):
    for index in range(len(str)):
        for substring in substrings:
            if equals_at(str, index, substring):
                return index

    return -1

def index_of_any_ignore_case(str, substrings):
    for index in range(len(str)):
        for substring in substrings:
            if equals_at_ignore_case(str, index, substring):
                return index

    return -1

def index_of_any_casefold(str, substrings):
    for index in range(len(str)):
        for substring in substrings:
            if equals_at_casefold(str, index, substring):
                return index

    return -1

def last_index_of(str, substring):
    return str.rindex(substring)

def last_index_of_ignore_case(str, substring):
    return str.lower().rfind(substring.lower())

def last_index_of_casefold(str, substring):
    return str.casefold().rfind(substring.casefold())

def last_index_of_any(str, substrings):
    for index in range(len(str) - 1, -1, -1):
        for substring in substrings:
            if equals_at(str, index, substring):
                return index

    return -1

def last_index_of_any_ignore_case(str, substrings):
    for index in range(len(str) - 1, -1, -1):
        for substring in substrings:
            if equals_at_ignore_case(str, index, substring):
                return index

    return -1

def last_index_of_any_casefold(str, substrings):
    for index in range(len(str) - 1, -1, -1):
        for substring in substrings:
            if equals_at_casefold(str, index, substring):
                return index

    return -1
