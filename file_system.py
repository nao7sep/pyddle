# Created: 2024-02-29
# This script contains file-system-related functions.

import os

def make_and_move_to_output_subdirectory():
    os.makedirs("output", exist_ok=True)
    os.chdir("output")
