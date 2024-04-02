# Created: 2024-02-29
# This script finds all Python-looking directories on all Windows drives / Mac volumes.

import os
import pyddle_debugging as pdebugging
import pyddle_string as pstring

def is_python_looking_directory(path):
    expected_directory_names = ['include', 'lib'] # These 2 are always expected.

    for name in expected_directory_names:
        if not os.path.isdir(os.path.join(path, name)):
            return False

    if pdebugging.is_debugging():
        print(f"Possible Python directory: {path}") # There can be variants of Python installations.

    expected_file_names = ['python3.exe', 'python.exe', 'python3', 'python']

    for name in expected_file_names:
        if os.path.isfile(os.path.join(path, name)):
            return True

    return False

def get_all_drive_or_volume_paths():
    if pstring.equals_ignore_case(os.name, 'nt'):
        for drive_letter in [chr(code) for code in range(ord('A'), ord('Z') + 1)]:
            if os.path.isdir(f"{drive_letter}:\\"):
                yield f"{drive_letter}:\\"

    else:
        for volume_name in os.listdir('/Volumes'):
            yield os.path.join('/Volumes', volume_name) # As a string.

scanned_directory_count = 0

for drive_or_volume_path in get_all_drive_or_volume_paths():
    # I dont mind using os.walk, which should be relatively slow, because this is a once-in-a-while script.
    # https://docs.python.org/3/library/os.html#os.walk
    # There must be faster ways to do this.
    for directory_path, subdirectory_names, _ in os.walk(drive_or_volume_path, onerror = None): # Explicitly ignore errors.
        scanned_directory_count += 1
        print(f"Scanned {scanned_directory_count} directories.\r", end = "")

        for subdirectory_name in subdirectory_names:
            subdirectory_path = os.path.join(directory_path, subdirectory_name)

            if is_python_looking_directory(subdirectory_path):
                print(f"Python-looking directory: {subdirectory_path}")

# In an non-debugging environment, the scanned directory count will be overwritten by the "Press Enter key" message.
# In a debugging environment, the console should get to a new prompt, with or without overwriting the last scanned directory count.

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
