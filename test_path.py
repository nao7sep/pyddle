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

# On Windows:
# os.path.basename(r"C:\Users\username\Documents\file.txt") => file.txt
# os.path.basename(r"/Users/username/Documents/file.txt") => file.txt
# os.path.basename(r"file.txt") => file.txt

# On Mac:
# os.path.basename(r"C:\Users\username\Documents\file.txt") => C:\Users\username\Documents\file.txt
# os.path.basename(r"/Users/username/Documents/file.txt") => file.txt
# os.path.basename(r"file.txt") => file.txt

debugging.try_evaluate(f'os.path.dirname(r"{windows_file_path}")')
debugging.try_evaluate(f'os.path.dirname(r"{mac_file_path}")')
debugging.try_evaluate(f'os.path.dirname(r"{file_name}")')

# On Windows:
# os.path.dirname(r"C:\Users\username\Documents\file.txt") => C:\Users\username\Documents
# os.path.dirname(r"/Users/username/Documents/file.txt") => /Users/username/Documents
# os.path.dirname(r"file.txt") =>

# On Mac:
# os.path.dirname(r"C:\Users\username\Documents\file.txt") =>
# os.path.dirname(r"/Users/username/Documents/file.txt") => /Users/username/Documents
# os.path.dirname(r"file.txt") =>

debugging.try_evaluate(f'os.path.splitext(r"{windows_file_path}")')
debugging.try_evaluate(f'os.path.splitext(r"{mac_file_path}")')
debugging.try_evaluate(f'os.path.splitext(r"{file_name}")')

# On Windows:
# os.path.splitext(r"C:\Users\username\Documents\file.txt") => ('C:\\Users\\username\\Documents\\file', '.txt')
# os.path.splitext(r"/Users/username/Documents/file.txt") => ('/Users/username/Documents/file', '.txt')
# os.path.splitext(r"file.txt") => ('file', '.txt')

# On Mac:
# os.path.splitext(r"C:\Users\username\Documents\file.txt") => ('C:\\Users\\username\\Documents\\file', '.txt')
# os.path.splitext(r"/Users/username/Documents/file.txt") => ('/Users/username/Documents/file', '.txt')
# os.path.splitext(r"file.txt") => ('file', '.txt')

debugging.display_press_enter_key_to_continue_if_not_debugging()
