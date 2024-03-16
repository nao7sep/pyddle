# Created: 2024-03-16
# A simple script to test path-related operations.

# import os => Seems to work without this.
import pyddle_debugging as debugging

windows_file_path = r'C:\Users\username\Documents\file.txt'
mac_file_path = '/Users/username/Documents/file.txt'
file_name = 'file.txt'

debugging.try_evaluate(f'os.path.basename(r"{windows_file_path}")')
debugging.try_evaluate(f'os.path.basename(r"{mac_file_path}")')
debugging.try_evaluate(f'os.path.basename(r"{file_name}")')

debugging.try_evaluate(f'os.path.dirname(r"{windows_file_path}")')
debugging.try_evaluate(f'os.path.dirname(r"{mac_file_path}")')
debugging.try_evaluate(f'os.path.dirname(r"{file_name}") == ""') # Compared with "".

debugging.try_evaluate(f'os.path.splitext(r"{windows_file_path}")')
debugging.try_evaluate(f'os.path.splitext(r"{mac_file_path}")')
debugging.try_evaluate(f'os.path.splitext(r"{file_name}")')

debugging.display_press_enter_key_to_continue_if_not_debugging()
