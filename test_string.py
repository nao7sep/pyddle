# Created: 2024-03-16
# A script to test pyddle_string.py and any string-related operations.

import pyddle_debugging as pdebugging
# pyddle_string must be imported in pyddle_debugging.

# ------------------------------------------------------------------------------
#     equals_at
# ------------------------------------------------------------------------------

# Starting with obvious cases.
pdebugging.try_evaluate('None.startswith("")')
pdebugging.try_evaluate('"".startswith(None)')

# "" and "" are obviously equal.
# Then, does "" technically start with ""?
pdebugging.try_evaluate('"".startswith("")')
pdebugging.try_evaluate('"a".startswith("")')
pdebugging.try_evaluate('"".startswith("a")') # The substring is longer.

# equals_at must act like startswith as they are both partial equality checkers.
# I dont think the error types need to be identical, but something must be raised in similar situations.
pdebugging.try_evaluate('pstring.equals_at(None, 0, "")')
pdebugging.try_evaluate('pstring.equals_at("", 0, None)')
pdebugging.try_evaluate('pstring.equals_at("", 0, "")') # Commented in the method's source code.

# Bad index.
pdebugging.try_evaluate('pstring.equals_at("", None, "")')
pdebugging.try_evaluate('pstring.equals_at("", -1, "")')
pdebugging.try_evaluate('pstring.equals_at("", 1, "")')

pdebugging.try_evaluate('pstring.equals_at("012", 1, "1")')
pdebugging.try_evaluate('pstring.equals_at("012", 1, "12")')
# A substring given to startswith may be longer than the source string.
pdebugging.try_evaluate('pstring.equals_at("012", 1, "123")')

# None.startswith("") => 'NoneType' object has no attribute 'startswith'
# "".startswith(None) => startswith first arg must be str or a tuple of str, not NoneType
# "".startswith("") => True
# "a".startswith("") => True
# "".startswith("a") => False
# pstring.equals_at(None, 0, "") => object of type 'NoneType' has no len()
# pstring.equals_at("", 0, None) => object of type 'NoneType' has no len()
# pstring.equals_at("", 0, "") => True
# pstring.equals_at("", None, "") => '<' not supported between instances of 'NoneType' and 'int'
# pstring.equals_at("", -1, "") => Index out of range.
# pstring.equals_at("", 1, "") => Index out of range.
# pstring.equals_at("012", 1, "1") => True
# pstring.equals_at("012", 1, "12") => True
# pstring.equals_at("012", 1, "123") => False

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

pdebugging.try_evaluate('None.find("")')
pdebugging.try_evaluate('"".find(None)')

pdebugging.try_evaluate('"".find("")') # Finds "" and returns 0.
pdebugging.try_evaluate('"a".find("")') # Again returns 0.
pdebugging.try_evaluate('"".find("a")')

pdebugging.try_evaluate('pyddle_string.index_of_any(None, [""])') # Must go through len(str).
pdebugging.try_evaluate('pyddle_string.index_of_any("", [None])') # Checked explicitly.

pdebugging.try_evaluate('pyddle_string.index_of_any("", [""])')
pdebugging.try_evaluate('pyddle_string.index_of_any("a", [""])')
pdebugging.try_evaluate('pyddle_string.index_of_any("", ["a"])')

# Again the edge-of-cliff situation described in pyddle_string.py occurs and 1 is returned.
# last_index_of_any too must explicitly return the length of the source string
#     when at least one of the substrings is "".

pdebugging.try_evaluate('"a".rfind("")')
pdebugging.try_evaluate('pyddle_string.last_index_of_any("a", [""])')

# Just making sure.
pdebugging.try_evaluate('pyddle_string.last_index_of_any("012", ["1"])')
pdebugging.try_evaluate('pyddle_string.last_index_of_any("012", ["3"])')

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

# ------------------------------------------------------------------------------
#     Line parts
# ------------------------------------------------------------------------------

pdebugging.try_evaluate('pyddle_string.split_line_into_parts(None)')
pdebugging.try_evaluate('pyddle_string.split_line_into_parts("")')
pdebugging.try_evaluate('pyddle_string.split_line_into_parts(" ")')
pdebugging.try_evaluate('pyddle_string.split_line_into_parts("a")')
pdebugging.try_evaluate('pyddle_string.split_line_into_parts(" a")')
pdebugging.try_evaluate('pyddle_string.split_line_into_parts("a ")')
pdebugging.try_evaluate('pyddle_string.split_line_into_parts(" a ")')
pdebugging.try_evaluate('pyddle_string.split_line_into_parts(" \\n ")')

# pyddle_string.split_line_into_parts(None) => (None, None, None)
# pyddle_string.split_line_into_parts("") => ('', '', '')
# pyddle_string.split_line_into_parts(" ") => (' ', '', '')
# pyddle_string.split_line_into_parts("a") => ('', 'a', '')
# pyddle_string.split_line_into_parts(" a") => (' ', 'a', '')
# pyddle_string.split_line_into_parts("a ") => ('', 'a', ' ')
# pyddle_string.split_line_into_parts(" a ") => (' ', 'a', ' ')
# pyddle_string.split_line_into_parts(" \n ") => (' \n ', '', '')

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
