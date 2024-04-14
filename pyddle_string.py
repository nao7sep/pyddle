# Created: 2024-03-05
# This script contains string-related functions.

import re
import unicodedata

import pyddle_debugging as pdebugging

LEVELED_INDENTS = [
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

def to_visible_str(str_):
    if str_ is None:
        return "(None)"

    if str_ == "":
        return "(Empty)"

    return str_

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

def contains(str_array, str_):
    for item in str_array:
        if equals(item, str_):
            return True

    return False

def contains_ignore_case(str_array, str_):
    for item in str_array:
        if equals_ignore_case(item, str_):
            return True

    return False

def contains_casefold(str_array, str_):
    for item in str_array:
        if equals_casefold(item, str_):
            return True

    return False

# ------------------------------------------------------------------------------
#     Partial equality
# ------------------------------------------------------------------------------

def startswith(str_, prefix):
    return str_.startswith(prefix)

def startswith_ignore_case(str_, prefix):
    return str_.lower().startswith(prefix.lower())

def startswith_casefold(str_, prefix):
    return str_.casefold().startswith(prefix.casefold())

# I wont implement startswith_any because we usually have something to do for each substring;
#     it would be better design to call startswith for each substring.

def equals_at(str_, index, substring):
    str_length = len(str_)
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

    if index + substring_length > len(str_):
        return False

    return str_[index : index + substring_length] == substring

def equals_at_ignore_case(str_, index, substring):
    str_length = len(str_)
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

    if index + substring_length > len(str_):
        return False

    return str_[index : index + substring_length].lower() == substring.lower()

def equals_at_casefold(str_, index, substring):
    str_length = len(str_)
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

    if index + substring_length > len(str_):
        return False

    return str_[index : index + substring_length].casefold() == substring.casefold()

def endswith(str_, suffix):
    return str_.endswith(suffix)

def endswith_ignore_case(str_, suffix):
    return str_.lower().endswith(suffix.lower())

def endswith_casefold(str_, suffix):
    return str_.casefold().endswith(suffix.casefold())

# ------------------------------------------------------------------------------
#     Searching
# ------------------------------------------------------------------------------

def index_of(str_, substring):
    return str_.find(substring)

def index_of_ignore_case(str_, substring):
    return str_.lower().find(substring.lower())

def index_of_casefold(str_, substring):
    return str_.casefold().find(substring.casefold())

def index_of_any(str_, substrings):
    # Checking for None, not caching.
    str_length = len(str_)

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
            if equals_at(str_, index, substring):
                return index

    return -1

def index_of_any_ignore_case(str_, substrings):
    str_length = len(str_)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        if substring == "":
            return 0

    for index in range(str_length):
        for substring in substrings:
            if equals_at_ignore_case(str_, index, substring):
                return index

    return -1

def index_of_any_casefold(str_, substrings):
    str_length = len(str_)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        if substring == "":
            return 0

    for index in range(str_length):
        for substring in substrings:
            if equals_at_casefold(str_, index, substring):
                return index

    return -1

# I thought about implementing contains_any, but we generally shouldnt implement methods
#     that just call other methods and (partially) discard the results.

def last_index_of(str_, substring):
    return str_.rfind(substring)

def last_index_of_ignore_case(str_, substring):
    return str_.lower().rfind(substring.lower())

def last_index_of_casefold(str_, substring):
    return str_.casefold().rfind(substring.casefold())

def last_index_of_any(str_, substrings):
    str_length = len(str_)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        if substring == "":
            # Not str_length - 1.
            # "a".rfind("") returns 1.
            return str_length

    for index in range(str_length - 1, -1, -1):
        for substring in substrings:
            if equals_at(str_, index, substring):
                return index

    return -1

def last_index_of_any_ignore_case(str_, substrings):
    str_length = len(str_)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        if substring == "":
            return str_length

    for index in range(str_length - 1, -1, -1):
        for substring in substrings:
            if equals_at_ignore_case(str_, index, substring):
                return index

    return -1

def last_index_of_any_casefold(str_, substrings):
    str_length = len(str_)

    for substring in substrings:
        if substring is None:
            raise RuntimeError("None is not a valid substring.")

        if substring == "":
            return str_length

    for index in range(str_length - 1, -1, -1):
        for substring in substrings:
            if equals_at_casefold(str_, index, substring):
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

def splitlines(str_: str | None, trim_line_start = False, trim_line_end = True,
               remove_empty_lines_at_start = True, remove_redundant_empty_lines = True, remove_empty_lines_at_end = True):
    ''' Splits a multiline string into lines and normalizes them. '''

    if not str_:
        # "".splitlines() returns an empty list.
        return []

    return normalize_lines(str_.splitlines(), trim_line_start = trim_line_start, trim_line_end = trim_line_end,
                           remove_empty_lines_at_start = remove_empty_lines_at_start, remove_redundant_empty_lines = remove_redundant_empty_lines, remove_empty_lines_at_end = remove_empty_lines_at_end)

# The method below was originally a part of the "splitlines" method.
# As Python doesnt have C#'s StringBuilder and such mechanisms may not be efficient,
#     I expect there'll be situations where strings are built line by line.

def normalize_lines(lines: list[str], trim_line_start = False, trim_line_end = True,
               remove_empty_lines_at_start = True, remove_redundant_empty_lines = True, remove_empty_lines_at_end = True):
    ''' Normalizes a list of lines by trimming them and removing empty lines. '''

    if not lines:
        # We dont need to raise an error just because "lines" is None.
        return []

    if trim_line_start:
        if trim_line_end:
            stripped_lines = [line.strip() for line in lines]

        else:
            stripped_lines = [line.lstrip() for line in lines]

    else:
        if trim_line_end:
            stripped_lines = [line.rstrip() for line in lines]

        else:
            stripped_lines = lines

    new_lines = []

    has_detected_visible_line = False # Whether at least one visible line has ever been detected.
    detected_continuous_empty_line_count = 0

    for stripped_line in stripped_lines:
        if not stripped_line:
            # Empty lines are added when a visible line is detected or at the end.
            detected_continuous_empty_line_count += 1

        else:
            if has_detected_visible_line is False: # Start part.
                has_detected_visible_line = True

                if remove_empty_lines_at_start is False:
                    for _ in range(detected_continuous_empty_line_count):
                        new_lines.append("")

            else: # Middle part.
                if detected_continuous_empty_line_count > 0:
                    if remove_redundant_empty_lines:
                        new_lines.append("")

                    else:
                        for _ in range(detected_continuous_empty_line_count):
                            new_lines.append("")

            detected_continuous_empty_line_count = 0
            new_lines.append(stripped_line)

    # End part.
    if detected_continuous_empty_line_count > 0:
        if remove_empty_lines_at_end is False:
            for _ in range(detected_continuous_empty_line_count):
                new_lines.append("")

    return new_lines

def normalize_multiline_str(str_, trim_line_start = False, trim_line_end = True,
                            remove_empty_lines_at_start = True, remove_redundant_empty_lines = True, remove_empty_lines_at_end = True):
    ''' Splits a multiline string into lines, normalizes them and joins them back. '''

    if not str_:
        return str_

    return "\n".join(splitlines(str_, trim_line_start, trim_line_end,
                                remove_empty_lines_at_start, remove_redundant_empty_lines, remove_empty_lines_at_end))

# ------------------------------------------------------------------------------
#     Normalization of single line strings
# ------------------------------------------------------------------------------

# "\s" matches new lines as well.
COMPILED_REGEX_FOR_NORMALIZE_SINGLELINE_STR = re.compile(r"\s+")

# This method is often an overkill.
# It may be useful in a situation where the input string can NEVER contain a line break
#     or any Unicode whitespace other than the ASCII space.

# In the implementation, what "\s" matches should be identical or very similar to what str.strip would remove.
# https://docs.python.org/3/library/stdtypes.html#str.strip
# https://docs.python.org/3/library/stdtypes.html#str.isspace
# https://docs.python.org/3/library/re.html#regular-expression-syntax

# Although the method removes a lot of Unicode whitespace,
#     there are characters that are essentially not very different from whitespace and are NOT removed,
#     one of which would be the right-to-left mark.
# I've seen situations where they were treated as whitespace, undefined characters, etc.
# Theoretically, RTL marks should be harmless when left within strings.
# https://en.wikipedia.org/wiki/Right-to-left_mark

# The application of this method is highly limited:

# One example would be when we parse a string in a certain format
#     and we dont want to care about line breaks, toggling some internal modes on and off.

# Also, when we take a title or a file name on an open system with a lot of anonymous users,
#     even though some endusers might not be comfortable with the system removing redundant whitespace,
#     doing so might help other users distinguish entries where only the KINDS of the whitespace characters differ.

# "abc  xyz.txt" and "abc　xyz.txt" for example should look very similar.
# The former contains a pair of ASCII space and the latter contains one ideographic space (U+3000),
#     which is a very frequently used space char in CJK workplaces.

# In many cases, especially when the users are all known and the system is closed,
#     this method would be an overkill.
# Some endusers just prefer to use ideographic space chars because:
#     1) They are more visible and/or 2) Their width is consistent with CJK characters surrounding them.

# Use this method only in cases where normalizing mid-string whitespace increases security significantly.

def normalize_singleline_str(str_, trim_start = True, remove_redundant_whitespace_chars = True, trim_end = True):
    ''' Call me only if you really need me. Otherwise, call "strip" instead. '''

    if not str_:
        return str_

    if trim_start:
        if trim_end:
            new_str = str_.strip()

        else:
            new_str = str_.lstrip()

    else:
        if trim_end:
            new_str = str_.rstrip()

        else:
            new_str = str_

    if remove_redundant_whitespace_chars:
        return COMPILED_REGEX_FOR_NORMALIZE_SINGLELINE_STR.sub(" ", new_str)

    else:
        return new_str

# ------------------------------------------------------------------------------
#     Line parts
# ------------------------------------------------------------------------------

# Here, a line is considered to be a tuple of 1) Indents, 2) Visible content, 3) Trailing whitespace.

# If the line is None or empty, a tuple with the same value set to each component is returned (to avoid the "not extracted" error).

# If the line contains only whitespace, as the (non-greedy) middle part and the last part of the regex have no reason to take the characters, everything goes to the first part.
# I would say "an empty visible content having all the leading whitespace characters as indents" is a natural perception.

# If the line contains line breaks, re.DOTALL lets "." match them and the matching should still succeed.
# At first, I checked is_debugging and raised an error, but that was overreacting, which only complicated the caller side's code.
# Calling this method on a line is technically inappropriate, but it is often harmless
#     while injecting a multiline string into a place where a singleline is expected may not be challenging.

# On the caller side, the best practice would be considering #1 and #3 to be empty if #2 is falsy.
# In many cases, a line only with invisible indents and trailing whitespace doesnt need to be processed.
# Then, if the visible content shouldnt contain a line break, make sure to check it.

COMPILED_REGEX_FOR_SPLIT_LINE_INTO_PARTS = re.compile(r"^(\s*)(.*?)(\s*)$", flags = re.DOTALL)

def split_line_into_parts(str_):
    if not str_:
        return (str_, str_, str_)

    match = COMPILED_REGEX_FOR_SPLIT_LINE_INTO_PARTS.match(str_)

    if pdebugging.is_debugging():
        if not match:
            # Unless the "re" module is implemented incorrectly, the number of groups should always be 3.
            raise RuntimeError(f"Line parts could not be extracted from \"{str_}\".")

    return match.groups()

# ------------------------------------------------------------------------------
#     ChunkStrReader
# ------------------------------------------------------------------------------

# I consider a "line break" is a complete string that works to break a line.
# Here, I say "chars" as chars that may be found in line breaks.

# In the following implementation and elsewhere, "\r\n" and "\n" are generally supported.
# Additionally, if "\r" is found and the next character is not "\n" or the string ends there, I believe it's OK to consider it a line break.
# When a string is being processed, no character should be able to crash the program.

LINE_BREAK_CHARS = ["\r", "\n"]

def get_line_break_len(str_, str_len, first_line_break_char_index):
    if str_[first_line_break_char_index] == "\r":
        if first_line_break_char_index + 1 < str_len:
            if str_[first_line_break_char_index + 1] == "\n":
                return 2

    return 1

class ChunkStrReader:
    def __init__(self, indents = ""):
        self.chunks = []
        self.indents = indents
        self.__first_indents_consumed = False # We must consider as if there had been a line break before the beginning of the string.

    def add_chunk(self, chunk):
        if chunk:
            self.chunks.append(chunk)

    def read_str(self, force = False):
        # If no chunk contains a line break char, it would be a singleline string when joined.

        for chunk_index, chunk in enumerate(self.chunks):
            line_break_index = index_of_any(chunk, LINE_BREAK_CHARS)

            # When we find one chunk containing a line break char (not necessarily a complete line break),
            #     we join the chunks up to that point as a singleline string and switch to the mode where "chunks_to_return" is populated.

            # If that string contains at least one character, even though they may be whitespace,
            #     as explained in the comments at the end of this method, the first indents are applied.

            if line_break_index >= 0:
                temp_str = "".join(self.chunks[0 : chunk_index])

                chunks_to_return = []

                if not self.__first_indents_consumed and temp_str:
                    chunks_to_return.append(self.indents)
                    self.__first_indents_consumed = True

                chunks_to_return.append(temp_str)

                # Now we have dealt with the singleline part.
                # We have a chunk that contains at least one line break char and 0 or more chunks after that.
                # As the first indents have been considered, we can deal with the rest as one joined string that contains 1 or more line break chars.

                remaining_str = "".join(self.chunks[chunk_index : ])
                remaining_str_len = len(remaining_str)

                char_index = 0

                while char_index < remaining_str_len: # The loop must be like this so that "char_index" can be adjusted.
                    char = remaining_str[char_index]

                    # When we meet a line break "char", we check the length of the line break and get the entire line break string.
                    # Then, depending on what follows, we decide whether to add the indents after the line break or not.

                    if char in LINE_BREAK_CHARS:
                        line_break_len = get_line_break_len(remaining_str, remaining_str_len, char_index)
                        line_break_str = remaining_str[char_index : char_index + line_break_len]

                        if char_index + line_break_len < remaining_str_len: # No way we can leave the loop from this block.
                            next_char = remaining_str[char_index + line_break_len]

                            # If the next character is another line break char, it cant be the second character of "\r\n" and it must be a empty line, which doesnt require indents.

                            if next_char in LINE_BREAK_CHARS:
                                chunks_to_return.append(line_break_str)
                                char_index += line_break_len

                            # If it's a non-line-break char, even though they may be whitespace, as explained in the comments at the end of this method, indents are applied before the next char.

                            else:
                                chunks_to_return.append(line_break_str)
                                chunks_to_return.append(self.indents)
                                char_index += line_break_len

                        # If there's no character after the line break, we need to wait for the next chunk(s) to know whether it'll be a new line or a non-line-break char.
                        # If "force" is False, as we are at the end of the string and are seeing a line break there, having dealt with all characters before it,
                        #     we clear the chunks, add just the line break to the list and return what we have collected so far.
                        # If "force" is True, assuming there wont be any more chunks, we add the line break to the list and return everything.

                        else:
                            if force: # Can leave the loop.
                                # self.chunks.clear() # Cleared after the loop.
                                chunks_to_return.append(line_break_str)
                                char_index += line_break_len

                            else: # Returns from here.
                                self.chunks.clear()
                                self.chunks.append(line_break_str)
                                return "".join(chunks_to_return)

                    # In this algorithm, a non-line-break char is not associated with any further actions.

                    else: # Can leave the loop.
                        chunks_to_return.append(char)
                        char_index += 1

                # If we have left the loop, it means we have dealt with all the characters 1) Including the last non-line-break char or 2) The last one was a line break char and "force" was True.
                # In either case, we clear the chunks and return what we have collected.

                self.chunks.clear()
                return "".join(chunks_to_return)

        # Returns the joined singleline string.

        # If the string is not empty, even though they might not be visible,
        #     there is at least one character that deserves to be indented if the first indents havent been consumed.
        # When the string is normalized, I dont add indents to lines that would be empty when normalized,
        #     but here the lines arent normalized and therefore one whitespace char alone could take the indentation.

        str_ = "".join(self.chunks)
        self.chunks.clear()

        if not self.__first_indents_consumed and str_:
            self.__first_indents_consumed = True
            return self.indents + str_

        return str_

# ------------------------------------------------------------------------------
#     Extraction of first part
# ------------------------------------------------------------------------------

# Considering Python's rules, 80 should be a good number.
# Then, in the UI, a place that can display 80 characters should be able to deal with 50% more characters.
# 80-100 too is a good option, but if we look for a punctuation char, expecting a more natural break, there should be a little more room.

def extract_first_part(str_, ideal_len = 80, max_len = 120, trailing = "..."):
    if not str_:
        return str_

    # When we want to extract the first part of a string, we dont want it to contain line breaks or redundant whitespace.

    normalized_str = normalize_singleline_str(str_)
    normalized_str_len = len(normalized_str)

    if normalized_str_len <= max_len:
        return normalized_str

    def _extract(category_first_letter):
        char_index = ideal_len

        while char_index < max_len:
            char = normalized_str[char_index]
            category = unicodedata.category(char)

            if category.startswith(category_first_letter):
                return normalized_str[0 : char_index].rstrip() + trailing

            char_index += 1

        return None

    # https://en.wikipedia.org/wiki/Unicode_character_property

    # Punctuations, symbols, separators in this order.
    first_part = _extract("P") or _extract("S") or _extract("Z")

    if first_part:
        return first_part

    # If it's a CJK string, it'd end up here.
    return normalized_str[0 : ideal_len].rstrip() + trailing
