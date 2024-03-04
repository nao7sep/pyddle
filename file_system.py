# Created: 2024-02-29
# This script contains file-system-related functions.

import os

def make_and_move_to_output_subdirectory():
    output_directory_path = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_directory_path, exist_ok=True)
    os.chdir(output_directory_path)
