# Created: 2024-03-05
# This script tests the core functionalities of the file_system module.

import pyddle_debugging as debugging
import pyddle_file_system as file_system

file_system.make_and_move_to_output_subdirectory()

for encoding, bom in file_system.utf_encodings_and_boms:
    encoding_in_lowercase = encoding.lower()
    file_name = f"test_file_system_{encoding_in_lowercase.replace("-", "_")}.txt"

    with file_system.open_file_and_write_utf_encoding_bom(file_name, encoding) as file:
        file.write(encoding)

    with file_system.open_file_and_detect_utf_encoding(file_name) as file:
        content = file.read()
        file.buffer.seek(0, 2)
        file_length = file.buffer.tell()
        print(f"{file_name}: {content} ({file_length} bytes)")

debugging.display_press_enter_key_to_continue_if_not_debugging()
