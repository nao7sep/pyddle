# Created: 2024-03-16
# A simple script to test path-related operations.

# import os => Seems to work without this.

import pyddle_debugging as pdebugging
# pyddle_path must be imported in pyddle_debugging.

WINDOWS_FILE_PATH = r'C:\Users\username\Documents\file.txt'
MAC_FILE_PATH = '/Users/username/Documents/file.txt'
FILE_NAME = 'file.txt'

pdebugging.try_evaluate(f'os.path.basename(r"{WINDOWS_FILE_PATH}")')
pdebugging.try_evaluate(f'os.path.basename(r"{MAC_FILE_PATH}")')
pdebugging.try_evaluate(f'os.path.basename(r"{FILE_NAME}")')

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

pdebugging.try_evaluate(f'os.path.dirname(r"{WINDOWS_FILE_PATH}")')
pdebugging.try_evaluate(f'os.path.dirname(r"{MAC_FILE_PATH}")')
pdebugging.try_evaluate(f'os.path.dirname(r"{FILE_NAME}")')

# On Windows:
# os.path.dirname(r"C:\Users\username\Documents\file.txt") => C:\Users\username\Documents
# os.path.dirname(r"/Users/username/Documents/file.txt") => /Users/username/Documents
# os.path.dirname(r"file.txt") =>

# Again, if the user develops and runs Python scripts only on Mac, the following behavior is reasonable.

# On Mac:
# os.path.dirname(r"C:\Users\username\Documents\file.txt") =>
# os.path.dirname(r"/Users/username/Documents/file.txt") => /Users/username/Documents
# os.path.dirname(r"file.txt") =>

pdebugging.try_evaluate(f'os.path.splitext(r"{WINDOWS_FILE_PATH}")')
pdebugging.try_evaluate(f'os.path.splitext(r"{MAC_FILE_PATH}")')
pdebugging.try_evaluate(f'os.path.splitext(r"{FILE_NAME}")')

# On Windows:
# os.path.splitext(r"C:\Users\username\Documents\file.txt") => ('C:\\Users\\username\\Documents\\file', '.txt')
# os.path.splitext(r"/Users/username/Documents/file.txt") => ('/Users/username/Documents/file', '.txt')
# os.path.splitext(r"file.txt") => ('file', '.txt')

# On Mac:
# os.path.splitext(r"C:\Users\username\Documents\file.txt") => ('C:\\Users\\username\\Documents\\file', '.txt')
# os.path.splitext(r"/Users/username/Documents/file.txt") => ('/Users/username/Documents/file', '.txt')
# os.path.splitext(r"file.txt") => ('file', '.txt')

# ------------------------------------------------------------------------------
#     basename/dirname
# ------------------------------------------------------------------------------

pdebugging.try_evaluate(f'ppath.basename(r"{WINDOWS_FILE_PATH}")')
pdebugging.try_evaluate(f'ppath.basename(r"{MAC_FILE_PATH}")')
pdebugging.try_evaluate(f'ppath.basename(r"{FILE_NAME}")')

# On Windows and Mac:
# ppath.basename(r"C:\Users\username\Documents\file.txt") => file.txt
# ppath.basename(r"/Users/username/Documents/file.txt") => file.txt
# ppath.basename(r"file.txt") => file.txt

pdebugging.try_evaluate(f'ppath.dirname(r"{WINDOWS_FILE_PATH}")')
pdebugging.try_evaluate(f'ppath.dirname(r"{MAC_FILE_PATH}")')
pdebugging.try_evaluate(f'ppath.dirname(r"{FILE_NAME}")')

# On Windows and Mac:
# ppath.dirname(r"C:\Users\username\Documents\file.txt") => C:\Users\username\Documents
# ppath.dirname(r"/Users/username/Documents/file.txt") => /Users/username/Documents
# ppath.dirname(r"file.txt") =>

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
