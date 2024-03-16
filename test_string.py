# Created: 2024-03-16
# A script to test pyddle_string.py and any string-related operations.

import pyddle_debugging as debugging
import pyddle_string # as string

def try_evaluate(code):
    try:
        print(f"{code} => {eval(code)}")

    except Exception as exception:
        print(f"{code} => {exception}")

# ------------------------------------------------------------------------------
#     equals_at
# ------------------------------------------------------------------------------

# Starting with obvious cases.
try_evaluate('None.startswith("")')
try_evaluate('"".startswith(None)')

# "" and "" are obviously equal.
# Then, does "" technically start with ""?
try_evaluate('"".startswith("")')
try_evaluate('"a".startswith("")')
try_evaluate('"".startswith("a")') # The substring is longer.

# equals_at must act like startswith as they are both partial equality checkers.
# I dont think the error types need to be identical, but something must be raised in similar situations.
try_evaluate('pyddle_string.equals_at(None, 0, "")')
try_evaluate('pyddle_string.equals_at("", 0, None)')
try_evaluate('pyddle_string.equals_at("", 0, "")') # Commented in the method's source code.

# Bad index.
try_evaluate('pyddle_string.equals_at("", None, "")')
try_evaluate('pyddle_string.equals_at("", -1, "")')
try_evaluate('pyddle_string.equals_at("", 1, "")')

try_evaluate('pyddle_string.equals_at("012", 1, "1")')
try_evaluate('pyddle_string.equals_at("012", 1, "12")')
# A substring given to startswith may be longer than the source string.
try_evaluate('pyddle_string.equals_at("012", 1, "123")')

# None.startswith("") => 'NoneType' object has no attribute 'startswith'
# "".startswith(None) => startswith first arg must be str or a tuple of str, not NoneType
# "".startswith("") => True
# "a".startswith("") => True
# "".startswith("a") => False
# pyddle_string.equals_at(None, 0, "") => object of type 'NoneType' has no len()
# pyddle_string.equals_at("", 0, None) => object of type 'NoneType' has no len()
# pyddle_string.equals_at("", 0, "") => True
# pyddle_string.equals_at("", None, "") => '<' not supported between instances of 'NoneType' and 'int'
# pyddle_string.equals_at("", -1, "") => Index out of range.
# pyddle_string.equals_at("", 1, "") => Index out of range.
# pyddle_string.equals_at("012", 1, "1") => True
# pyddle_string.equals_at("012", 1, "12") => True
# pyddle_string.equals_at("012", 1, "123") => False

# ------------------------------------------------------------------------------
#     index_of_any/last_index_of_any
# ------------------------------------------------------------------------------

# Python doesnt seem to have a built-in method like C#'s String.IndexOfAny.
# https://learn.microsoft.com/en-us/dotnet/api/system.string.indexofany

# Python doesnt even have a char type.
# https://developers.google.com/edu/python/strings

# Having been developing in other programming languages for a while,
#     I feel extremely wrong about extracting each character as a single-char string for comparison.
# But if that's the way it is, we shouldnt mind a few highly inefficient methods that just get things done.

# I expect index_of to work like C#'s String.IndexOf, returning -1 when the substring is not found.
# index_of_any must raise an error when index_of(each_substring) would.

try_evaluate('None.find("")')
try_evaluate('"".find(None)')

try_evaluate('"".find("")') # Finds "" and returns 0.
try_evaluate('"a".find("")') # Again returns 0.
try_evaluate('"".find("a")')

try_evaluate('pyddle_string.index_of_any(None, [""])') # Must go through len(str).
try_evaluate('pyddle_string.index_of_any("", [None])') # Checked explicitly.

try_evaluate('pyddle_string.index_of_any("", [""])')
try_evaluate('pyddle_string.index_of_any("a", [""])')
try_evaluate('pyddle_string.index_of_any("", ["a"])')

# Again the edge-of-cliff situation described in pyddle_string.py occurs and 1 is returned.
# last_index_of_any too must explicitly return the length of the source string
#     when at least one of the substrings is "".

try_evaluate('"a".rfind("")')
try_evaluate('pyddle_string.last_index_of_any("a", [""])')

# Just making sure.
try_evaluate('pyddle_string.last_index_of_any("012", ["1"])')
try_evaluate('pyddle_string.last_index_of_any("012", ["3"])')

# None.find("") => 'NoneType' object has no attribute 'find'
# "".find(None) => must be str, not NoneType
# "".find("") => 0
# "a".find("") => 0
# "".find("a") => -1
# pyddle_string.index_of_any(None, [""]) => object of type 'NoneType' has no len()
# pyddle_string.index_of_any("", [None]) => None is not a valid substring.
# pyddle_string.index_of_any("", [""]) => 0
# pyddle_string.index_of_any("a", [""]) => 0
# pyddle_string.index_of_any("", ["a"]) => -1
# "a".rfind("") => 1
# pyddle_string.last_index_of_any("a", [""]) => 1
# pyddle_string.last_index_of_any("012", ["1"]) => 1
# pyddle_string.last_index_of_any("012", ["3"]) => -1

debugging.display_press_enter_key_to_continue_if_not_debugging()
