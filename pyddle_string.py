# Created: 2024-03-05
# This script contains string-related functions.

import re

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

# ------------------------------------------------------------------------------
#     Multiline strings
# ------------------------------------------------------------------------------

# Methods for conversion/transformation should generally deal with None and "" nicely, not raising errors.
# They are casually called to make things a little better if there's any room for improvement.

# Those for equality/comparison, on the other hand, MAY raise errors if None is provided
#     because there's a high chance that the developer is doing something wrong.
# Like, startswith(None, "a") is most likely not an intended operation.

def splitlines(str, trim_line_start=False, trim_line_end=True,
               remove_empty_lines_at_start=True, remove_redundant_empty_lines=True, remove_empty_lines_at_end=True):
    ''' Does more than Python's splitlines by default. '''

    if not str:
        # "".splitlines() returns an empty list.
        return []

    raw_lines = str.splitlines()

    if trim_line_start:
        if trim_line_end:
            stripped_lines = [raw_line.strip() for raw_line in raw_lines]

        else:
            stripped_lines = [raw_line.lstrip() for raw_line in raw_lines]

    else:
        if trim_line_end:
            stripped_lines = [raw_line.rstrip() for raw_line in raw_lines]

        else:
            stripped_lines = raw_lines

    lines = []

    has_detected_visible_line = False # Whether at least one visible line has ever been detected.
    detected_continuous_empty_line_count = 0

    for stripped_line in stripped_lines:
        if not stripped_line:
            # Empty lines are added when a visible line is detected or at the end.
            detected_continuous_empty_line_count += 1

        else:
            if has_detected_visible_line == False: # Start part.
                has_detected_visible_line = True

                if remove_empty_lines_at_start == False:
                    for _ in range(detected_continuous_empty_line_count):
                        lines.append("")

            else: # Middle part.
                if detected_continuous_empty_line_count > 0:
                    if remove_redundant_empty_lines:
                        lines.append("")

                    else:
                        for _ in range(detected_continuous_empty_line_count):
                            lines.append("")

            detected_continuous_empty_line_count = 0
            lines.append(stripped_line)

    # End part.
    if detected_continuous_empty_line_count > 0:
        if remove_empty_lines_at_end == False:
            for _ in range(detected_continuous_empty_line_count):
                lines.append("")

    return lines

def normalize_multiline_str(str, trim_line_start=False, trim_line_end=True,
                            remove_empty_lines_at_start=True, remove_redundant_empty_lines=True, remove_empty_lines_at_end=True):
    if not str:
        return str

    return "\n".join(splitlines(str, trim_line_start, trim_line_end,
                                remove_empty_lines_at_start, remove_redundant_empty_lines, remove_empty_lines_at_end))

# ------------------------------------------------------------------------------
#     Normalization of single line strings
# ------------------------------------------------------------------------------

compiled_regex_for_normalize_singleline_str = re.compile(r"\s+")

def normalize_singleline_str(str, trim_start=True, remove_redundant_whitespace_chars=True, trim_end=True):
    if not str:
        return str

    if trim_start:
        if trim_end:
            new_str = str.strip()

        else:
            new_str = str.lstrip()

    else:
        if trim_end:
            new_str = str.rstrip()

        else:
            new_str = str

    if remove_redundant_whitespace_chars:
        return compiled_regex_for_normalize_singleline_str.sub(" ", new_str)

    else:
        return new_str

# ------------------------------------------------------------------------------
#     Line parts
# ------------------------------------------------------------------------------

# The following methods consider that a line is composed of three parts:
#     * Indents
#     * Visible content
#     * Trailing whitespace

# The middle part is not greedy.
# https://docs.python.org/3/library/re.html#regular-expression-syntax
compiled_regex_for_split_line_into_parts = re.compile(r"^(\s*)(.*?)(\s*)$")

def split_line_into_parts(line: str):
    ''' Returns a tuple of indents, visible content and trailing whitespace. '''

    if not line:
        return ("", "", "")

    # If the pattern contains ^ and $, is there a good reason to use fullmatch? :S
    match = compiled_regex_for_split_line_into_parts.match(line)

    # We could set "default" to the string we'd like any non-participating group of the match to be.
    # Here, every group should match something.
    # https://docs.python.org/3/library/re.html#re.Match.groups
    return match.groups()

def add_indents_and_trailing_whitespace_to_parts(
        parts: tuple[str, str, str], indents: str="", trailing_whitespace: str=""):
    return (parts[0] + indents, parts[1], trailing_whitespace + parts[2])

# When "str" is falsy, pyddle_string.splitlines returns an empty list just like "".splitlines().
# "build_multiline_parts" is designed to be consistent with that behavior.

# This method is often used to display something like:
# Lines:
#     Line 1
#     Line 2

# When there's no line, the code has to know it and omit the "Lines:" part as well,
#     rather than expecting "build_multiline_parts" to return an empty line or a suitable message.
# So, although the implementation doesnt explicitly raise an error when "str" is falsy,
#     let's say the behavior in such a case is undefined.

def build_multiline_parts(str, indents="", trailing_whitespace="", trim_line_start=False, trim_line_end=True,
                          remove_empty_lines_at_start=True, remove_redundant_empty_lines=True, remove_empty_lines_at_end=True):
    ''' Takes a multiline string and returns a list of tuples. When "str" is falsy, the behavior is undefined. '''

    new_lines = []

    for line in splitlines(str, trim_line_start, trim_line_end,
                           remove_empty_lines_at_start, remove_redundant_empty_lines, remove_empty_lines_at_end):
        parts = split_line_into_parts(line)
        new_parts = add_indents_and_trailing_whitespace_to_parts(parts, indents, trailing_whitespace)
        new_lines.append(new_parts)

    return new_lines

def build_singleline_parts(str, indents="", trailing_whitespace="",
                           trim_start=True, remove_redundant_whitespace_chars=True, trim_end=True):
    ''' Takes a singleline string and returns a tuple. '''

    # If "str" is falsy, normalize_singleline_str returns it as-is and split_line_into_parts takes care of it.

    normalized_str = normalize_singleline_str(str, trim_start, remove_redundant_whitespace_chars, trim_end)
    parts = split_line_into_parts(normalized_str)
    return add_indents_and_trailing_whitespace_to_parts(parts, indents, trailing_whitespace)
