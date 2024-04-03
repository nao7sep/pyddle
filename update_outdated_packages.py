# Created 2024-02-21
# This script updates all outdated packages.

import importlib.util
import json
import os
import subprocess
import sys

import pyddle_debugging as pdebugging
import pyddle_path as ppath
import pyddle_string as pstring

# Get the path to the directory containing the current Python executable.

print("Python executable: ", sys.executable)

directory_path = ppath.dirname(sys.executable)

# Get the path to the pip executable.

SUBDIRECTORY_NAMES = ["Scripts", "bin", None]
PIP_FILE_NAMES = ["pip3.exe", "pip.exe", "pip3", "pip"]

def get_pip_file_path():
    for subdirectory_name in SUBDIRECTORY_NAMES:
        for pip_file_name in PIP_FILE_NAMES:
            if subdirectory_name is not None:
                pip_file_path_ = os.path.join(directory_path, subdirectory_name, pip_file_name)

            else:
                pip_file_path_ = os.path.join(directory_path, pip_file_name)

            if os.path.isfile(pip_file_path_):
                return pip_file_path_

pip_file_path = get_pip_file_path()

if pip_file_path is None:
    print("pip executable not found.")
    sys.exit()

print("pip executable: ", pip_file_path)

# Update the pip itself.

subprocess.run([pip_file_path, "install", "--upgrade", "pip"], check=False)

# If the script is being debugged, older versions of the packages are installed to demonstrate the update process.

# Uninstall the tzdata package.
# It's required to run output_available_timezones.py and will be reinstalled later.

if pdebugging.is_debugging():
    subprocess.run([pip_file_path, "uninstall", "tzdata", "-y"], check=False)

# Install tzdata 2023.4, which is obsolete, for testing purposes.

if pdebugging.is_debugging():
    subprocess.run([pip_file_path, "install", "tzdata\u003D\u003D2023.4"], check=False)

# Remember whether beautifulsoup4 was originally installed.
# Oh well, I just liked the name of the package.

if pdebugging.is_debugging():
    is_beautifulsoup4_originally_installed = importlib.util.find_spec("beautifulsoup4") is not None

# Attempt to uninstall beautifulsoup4.

if pdebugging.is_debugging():
    subprocess.run([pip_file_path, "uninstall", "beautifulsoup4", "-y"], check=False)

# Install beautifulsoup4 4.12.2, which is obsolete, for testing purposes.

if pdebugging.is_debugging():
    subprocess.run([pip_file_path, "install", "beautifulsoup4\u003D\u003D4.12.2"], check=False)

# Get a list of all outdated packages as a JSON string.

outdated_packages_string = subprocess.run([pip_file_path, "list", "--outdated", "--format", "json"], capture_output=True, text=True, check=False).stdout

# Deserialize the JSON string.

outdated_packages = json.loads(outdated_packages_string)

if len(outdated_packages) > 0:
    print("Outdated packages:")

    for package in outdated_packages:
        print(f'    {package["name"]} {package["version"]} => {package["latest_version"]}')

    if pstring.equals_ignore_case(input("Would you like to update all outdated packages? (y/n) "), "y"):
        for package in outdated_packages:
            # Specify the version to avoid installing a newer version than intended.
            subprocess.run([pip_file_path, "install", f'{package["name"]}\u003D\u003D{package["latest_version"]}'], check=False)

else:
    print("No outdated packages.")

if pdebugging.is_debugging():
    if not is_beautifulsoup4_originally_installed:
        subprocess.run([pip_file_path, "uninstall", "beautifulsoup4", "-y"], check=False)

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
