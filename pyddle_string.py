# Created: 2024-03-05
# This script contains string-related functions.

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

def startswith(str, prefix):
    return str.startswith(prefix)

def startswith_ignore_case(str, prefix):
    return str.lower().startswith(prefix.lower())

def startswith_casefold(str, prefix):
    return str.casefold().startswith(prefix.casefold())

def endswith(str, suffix):
    return str.endswith(suffix)

def endswith_ignore_case(str, suffix):
    return str.lower().endswith(suffix.lower())

def endswith_casefold(str, suffix):
    return str.casefold().endswith(suffix.casefold())
