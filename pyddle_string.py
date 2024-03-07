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
