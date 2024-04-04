# Created: 2024-04-01
# Tests the pyddle_output module.

import pyddle_console as pconsole
import pyddle_debugging as pdebugging
import pyddle_global as pglobal
import pyddle_logging as plogging
import pyddle_output as poutput
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

# ------------------------------------------------------------------------------
#     print_and_log
# ------------------------------------------------------------------------------

# The following code only outputs things and doesnt verify them because:
#     1) Coloring is hard to verify automatically
#     2) This is a one-time test

BORDERLINE = "--------------------------------------------------------------------------------"

LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE = "    a    "

# Only "str_".
poutput.print_and_log(None)
poutput.print_and_log(BORDERLINE)
poutput.print_and_log("")
poutput.print_and_log(BORDERLINE)
poutput.print_and_log(LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE)

# One additional parameter.
poutput.print_and_log(BORDERLINE)
poutput.print_and_log(LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE, indents=pstring.LEVELED_INDENTS[1])
poutput.print_and_log(BORDERLINE)
poutput.print_and_log(LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE, colors=pconsole.IMPORTANT_COLORS)
poutput.print_and_log(BORDERLINE)
poutput.print_and_log(LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE, end="")
poutput.print_and_log("b") # Makes sure "end" was effective.

# One pair of parameters.
# Probably, this is the only meaningful pair.
poutput.print_and_log(BORDERLINE)
poutput.print_and_log(LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE, indents=pstring.LEVELED_INDENTS[1], colors=pconsole.IMPORTANT_COLORS)

# ------------------------------------------------------------------------------
#     print_and_log_lines
# ------------------------------------------------------------------------------

SINGLELINE_LIST = [LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE]
MULTILINE_LIST = [LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE, LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE]
MULTILINE_LIST_WITH_REDUNDANT_LINES = ["", LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE, "", "", LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE, ""]
NORMALIZED_MULTILINE_LIST = pstring.normalize_lines(MULTILINE_LIST)

# Only "str_".
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(None)
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines([None])
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines([""])
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(SINGLELINE_LIST)
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(MULTILINE_LIST)
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(MULTILINE_LIST_WITH_REDUNDANT_LINES)
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(NORMALIZED_MULTILINE_LIST)

# One additional parameter.
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(MULTILINE_LIST_WITH_REDUNDANT_LINES, indents=pstring.LEVELED_INDENTS[1])
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(MULTILINE_LIST_WITH_REDUNDANT_LINES, colors=pconsole.IMPORTANT_COLORS)
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(MULTILINE_LIST_WITH_REDUNDANT_LINES, trailing=LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE)
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(MULTILINE_LIST_WITH_REDUNDANT_LINES, end="")
poutput.print_and_log("b") # Makes sure "end" was effective.
# As "end" doesnt affect other parameters, we wont be testing it any more.

# One pair of parameters.
# 2nd-3rd, 2nd-4th, 3rd-4th only.
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(MULTILINE_LIST_WITH_REDUNDANT_LINES, indents=pstring.LEVELED_INDENTS[1], colors=pconsole.IMPORTANT_COLORS)
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(MULTILINE_LIST_WITH_REDUNDANT_LINES, indents=pstring.LEVELED_INDENTS[1], trailing=LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE)
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(MULTILINE_LIST_WITH_REDUNDANT_LINES, colors=pconsole.IMPORTANT_COLORS, trailing=LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE)

# 3 parameters.
poutput.print_and_log(BORDERLINE)
poutput.print_and_log_lines(MULTILINE_LIST_WITH_REDUNDANT_LINES, indents=pstring.LEVELED_INDENTS[1], colors=pconsole.IMPORTANT_COLORS, trailing=LINE_WITH_INDENTS_AND_TRAILING_WHITESPACE)

plogging.flush()

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
