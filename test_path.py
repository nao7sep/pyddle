# Created: 2024-03-16
# A simple script to test path-related operations.

# import os => Seems to work without this.
import pyddle_debugging as pdebugging
# pyddle_path must be imported in pyddle_debugging.

windows_file_path = r'C:\Users\username\Documents\file.txt'
mac_file_path = '/Users/username/Documents/file.txt'
file_name = 'file.txt'

pdebugging.try_evaluate(f'os.path.basename(r"{windows_file_path}")')
pdebugging.try_evaluate(f'os.path.basename(r"{mac_file_path}")')
pdebugging.try_evaluate(f'os.path.basename(r"{file_name}")')

# On Windows:
# os.path.basename(r"C:\Users\username\Documents\file.txt") => file.txt
# os.path.basename(r"/Users/username/Documents/file.txt") => file.txt
# os.path.basename(r"file.txt") => file.txt

# The combination of build_changed_projects.py and pyddle_dotnet.py failed to work on Mac.
# Somehow, os.path.basename couldnt extract the file name from "..\yyGptBookLib\yyGptBookLib.csproj".
# Now we know os.path.basename MAY NOT contain a multi-platform implementation.

# This is actually not a bug.
# Mac's file system allows a lot more chars in paths than Windows.
# Like, "C:\\Repositories\\pyddle\\data\\tasks.json" could be created as a valid file on Mac,
#     when I accidentally ran low_priority_queue.py before configuring it.

# But it's already an universal courtesy to avoid all platform's reserved chars in paths.
# So, there should be a few multi-platform methods to handle paths.

# On Mac:
# os.path.basename(r"C:\Users\username\Documents\file.txt") => C:\Users\username\Documents\file.txt
# os.path.basename(r"/Users/username/Documents/file.txt") => file.txt
# os.path.basename(r"file.txt") => file.txt

pdebugging.try_evaluate(f'os.path.dirname(r"{windows_file_path}")')
pdebugging.try_evaluate(f'os.path.dirname(r"{mac_file_path}")')
pdebugging.try_evaluate(f'os.path.dirname(r"{file_name}")')

# On Windows:
# os.path.dirname(r"C:\Users\username\Documents\file.txt") => C:\Users\username\Documents
# os.path.dirname(r"/Users/username/Documents/file.txt") => /Users/username/Documents
# os.path.dirname(r"file.txt") =>

# Again, if the user develops and runs Python scripts only on Mac, the following behavior is reasonable.

# On Mac:
# os.path.dirname(r"C:\Users\username\Documents\file.txt") =>
# os.path.dirname(r"/Users/username/Documents/file.txt") => /Users/username/Documents
# os.path.dirname(r"file.txt") =>

pdebugging.try_evaluate(f'os.path.splitext(r"{windows_file_path}")')
pdebugging.try_evaluate(f'os.path.splitext(r"{mac_file_path}")')
pdebugging.try_evaluate(f'os.path.splitext(r"{file_name}")')

# On Windows:
# os.path.splitext(r"C:\Users\username\Documents\file.txt") => ('C:\\Users\\username\\Documents\\file', '.txt')
# os.path.splitext(r"/Users/username/Documents/file.txt") => ('/Users/username/Documents/file', '.txt')
# os.path.splitext(r"file.txt") => ('file', '.txt')

# On Mac:
# os.path.splitext(r"C:\Users\username\Documents\file.txt") => ('C:\\Users\\username\\Documents\\file', '.txt')
# os.path.splitext(r"/Users/username/Documents/file.txt") => ('/Users/username/Documents/file', '.txt')
# os.path.splitext(r"file.txt") => ('file', '.txt')

# ------------------------------------------------------------------------------
#     pyddle_path.basename/dirname
# ------------------------------------------------------------------------------

pdebugging.try_evaluate(f'pyddle_path.basename(r"{windows_file_path}")')
pdebugging.try_evaluate(f'pyddle_path.basename(r"{mac_file_path}")')
pdebugging.try_evaluate(f'pyddle_path.basename(r"{file_name}")')

# On Windows and Mac:
# pyddle_path.basename(r"C:\Users\username\Documents\file.txt") => file.txt
# pyddle_path.basename(r"/Users/username/Documents/file.txt") => file.txt
# pyddle_path.basename(r"file.txt") => file.txt

pdebugging.try_evaluate(f'pyddle_path.dirname(r"{windows_file_path}")')
pdebugging.try_evaluate(f'pyddle_path.dirname(r"{mac_file_path}")')
pdebugging.try_evaluate(f'pyddle_path.dirname(r"{file_name}")')

# On Windows and Mac:
# pyddle_path.dirname(r"C:\Users\username\Documents\file.txt") => C:\Users\username\Documents
# pyddle_path.dirname(r"/Users/username/Documents/file.txt") => /Users/username/Documents
# pyddle_path.dirname(r"file.txt") =>

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
