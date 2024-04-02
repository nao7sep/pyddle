# Created: 2024-04-01
# Tests the pyddle_output module.

import pyddle_global as global
global.set_main_script_file_path(__file__)

import pyddle_debugging as pdebugging
import pyddle_logging as logging
import pyddle_output as output

# The following code only outputs things and doesnt verify them because:
#     1) Coloring is hard to verify automatically
#     2) This is a one-time test

output.print_and_log(None)
output.print_and_log("")

logging.flush()

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
