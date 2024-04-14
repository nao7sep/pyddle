# Created: 2024-03-05
# This script tests the core functionalities of the file_system module.

import os

import pyddle_debugging as pdebugging
import pyddle_file_system as pfs
import pyddle_global as pglobal

pglobal.set_main_script_file_path(__file__)

pfs.make_and_move_to_output_subdirectory()

for encoding, bom in pfs.UTF_ENCODINGS_AND_BOMS:
    encoding_in_lowercase = encoding.lower() # pylint: disable = invalid-name
    file_name = f"test_file_system_{encoding_in_lowercase.replace("-", "_")}.txt"

    with pfs.open_file_and_write_utf_encoding_bom(file_name, encoding) as file:
        file.write(encoding)

    with pfs.open_file_and_detect_utf_encoding(file_name) as file:
        content = file.read()
        file.buffer.seek(0, os.SEEK_END)
        file_length = file.buffer.tell()
        print(f"{file_name}: {content} ({file_length} bytes)")

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
