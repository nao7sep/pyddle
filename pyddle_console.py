# Created: 2024-03-07
# This script contains utility functions for console output/input.

from builtins import print as builtin_print
import colorama
import pyddle_string as string
import pyddle_type as type

# Specified colors appear differently depending on the platform.
# These should be an acceptable starting point.

def print_with_prefix_and_suffix(str, prefix, suffix, multiline=False, indents="", end="\n"):
    if multiline:
        for parts in string.build_multiline_parts(str, indents=indents):
            # If parts[1] is falsy, parts[0] will automatically be an empty string.
            # As a result of normalization and adding no trailing whitespace, parts[2] is always falsy.
            builtin_print(f"{parts[0]}{prefix if parts[1] else ''}{parts[1]}{suffix if parts[1] else ''}", end=end)

    else:
        # If "multiline" is False, we must also expect little-by-little output (like one portion is only ": " to separate a key and a value).
        # So, unless "str" is falsy, we must output the whole content of it as-is.

        # Added: If "str" is empty, only "end" is printed, which is an ideal behavior.
        # If "str" contains only whitespace characters, it goes to the first part,
        #     effectively printing the invisible string, often as a padding or a separator.

        parts = string.build_singleline_parts(str, indents=indents, trim_start=False, remove_redundant_whitespace_chars=False, trim_end=False)
        builtin_print(f"{parts[0]}{prefix if parts[1] else ''}{parts[1]}{suffix if parts[1] else ''}{parts[2]}", end=end)

def print(str, multiline=False, indents="", end="\n"):
    print_with_prefix_and_suffix(str, "", "", multiline=multiline, indents=indents, end=end)

prefix_for_print_important = colorama.Back.BLUE + colorama.Fore.WHITE
suffix_for_print_important = colorama.Style.RESET_ALL

def print_important(str, multiline=False, indents="", end="\n"):
    print_with_prefix_and_suffix(str, prefix_for_print_important, suffix_for_print_important, multiline=multiline, indents=indents, end=end)

prefix_for_print_warning = colorama.Back.YELLOW + colorama.Fore.BLACK
suffix_for_print_warning = colorama.Style.RESET_ALL

def print_warning(str, multiline=False, indents="", end="\n"):
    print_with_prefix_and_suffix(str, prefix_for_print_warning, suffix_for_print_warning, multiline=multiline, indents=indents, end=end)

prefix_for_print_error = colorama.Back.RED + colorama.Fore.WHITE
suffix_for_print_error = colorama.Style.RESET_ALL

def print_error(str, multiline=False, indents="", end="\n"):
    print_with_prefix_and_suffix(str, prefix_for_print_error, suffix_for_print_error, multiline=multiline, indents=indents, end=end)

# ------------------------------------------------------------------------------
#     Typical output/input operations
# ------------------------------------------------------------------------------

def print_numbered_options(options, indents="", end="\n"):
    ''' Space-pads the indices. '''

    digit_count = len(str(len(options))) # Wont be a negative number.

    for index, option in enumerate(options):
        padded_index_str = str(index + 1).rjust(digit_count, " ")
        print(f"{indents}{padded_index_str}. {option}", end=end)

def input_number(prompt, indents=""):
    ''' Returns None if the input is not a number. '''

    return type.str_to_int_or_default(input(f"{indents}{prompt}"), None)

class CommandInfo:
    def __init__(self, command, args):
        self.command = command
        self.args = args

    def get_arg(self, index):
        return self.args[index]

    def get_arg_or_default(self, index, default):
        if index < len(self.args):
            return self.args[index]

        return default

    def get_arg_as_int(self, index):
        return int(self.args[index])

    def get_arg_as_int_or_default(self, index, default):
        if index < len(self.args):
            return type.str_to_int_or_default(self.args[index], default)

        return default

    def get_arg_as_float(self, index):
        return float(self.args[index])

    def get_arg_as_float_or_default(self, index, default):
        if index < len(self.args):
            return type.str_to_float_or_default(self.args[index], default)

        return default

    def get_arg_as_complex(self, index):
        return complex(self.args[index])

    def get_arg_as_complex_or_default(self, index, default):
        if index < len(self.args):
            return type.str_to_complex_or_default(self.args[index], default)

        return default

    def get_arg_as_bool(self, index):
        return type.str_to_bool(self.args[index])

    def get_arg_as_bool_or_default(self, index, default):
        if index < len(self.args):
            return type.str_to_bool_or_default(self.args[index], default)

        return default

    # last_index may be confusing because we dont know if it's inclusive or exclusive.
    # But I dont want to use names like exclusive_end_index too much.
    def get_args(self, index, length):
        return self.args[index : index + length]

    def get_args_as_str(self, index, length, separator=" "):
        return separator.join(self.get_args(index, length))

    def get_remaining_args(self, index):
        return self.args[index:]

    # Should be useful for something like "add Hoge Moge Poge" where "Hoge Moge Poge" is one name for example.
    def get_remaining_args_as_str(self, index, separator=" "):
        return separator.join(self.get_remaining_args(index))

    def to_string(self, indents=""):
        ''' For debugging purposes. '''

        lines = []

        lines.append(f"{indents}Command: {self.command}")

        if len(self.args) > 0:
            lines.append(f"{indents}Arguments:")

            for index, arg in enumerate(self.args):
                # One level of indentation is added.
                # The indices shouldnt be space-padded within the brackets.
                # The closing bracket effectively separates the index from the argument, making a following colon unnecessary.
                lines.append(f"{indents}{string.leveledIndents[1]}[{index}] {string.to_visible_str(arg)}")

        return "\n".join(lines)

def parse_command_str(str):
    ''' Returns None if the command string is empty. '''

    # A smart function that recognizes a chain of any whitespace chars as one separator by default.

    parts = str.split()

    if len(parts) > 0:
        command = parts[0]
        args = parts[1:]

        return CommandInfo(command, args)

    return None

def input_command(prompt, indents=""):
    return parse_command_str(input(f"{indents}{prompt}"))
