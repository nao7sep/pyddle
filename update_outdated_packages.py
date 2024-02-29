# Created 2024-02-21
# This script updates all outdated packages.

# Get the path to the directory containing the current Python executable.

import sys
import os

directoryPath = os.path.dirname(sys.executable)

# Get the path to the pip executable.

def createPipFilePath(directoryPath: str, fileName: str) -> str:
    return os.path.join(directoryPath, "Scripts", f"{fileName}{os.name == 'nt' and '.exe' or ''}")

pipFilePath = createPipFilePath(directoryPath, "pip3") # Expect pip3 first.

if os.path.exists(pipFilePath) == False:
    pipFilePath = createPipFilePath(directoryPath, "pip") # Fall back to pip.

# Uninstall the tzdata package.
# It's required to run OutputAvailableTimezones.py and will be reinstalled later.

import subprocess

subprocess.run([pipFilePath, "uninstall", "tzdata", "-y"])

# Install tzdata 2023.4, which is obsolete, for testing purposes.

subprocess.run([pipFilePath, "install", "tzdata==2023.4"])

# Remember whether beautifulsoup4 was originally installed.
# Oh well, I just liked the name of the package.

import importlib.util

isBeautifulSoup4OriginallyInstalled = importlib.util.find_spec("beautifulsoup4") is not None

# Attempt to uninstall beautifulsoup4.

subprocess.run([pipFilePath, "uninstall", "beautifulsoup4", "-y"])

# Install beautifulsoup4 4.12.2, which is obsolete, for testing purposes.

subprocess.run([pipFilePath, "install", "beautifulsoup4==4.12.2"])

# Get a list of all outdated packages as a JSON string.

outdatedPackagesString = subprocess.run([pipFilePath, "list", "--outdated", "--format", "json"], capture_output=True, text=True).stdout

# Deserialize the JSON string.

import json

outdatedPackages = json.loads(outdatedPackagesString)

if len(outdatedPackages) > 0:
    print("Outdated packages:")

    for package in outdatedPackages:
        print(f'    {package["name"]} {package["version"]} => {package["latest_version"]}')

    if input("Would you like to update all outdated packages? (y/n) ").lower() == "y":
        for package in outdatedPackages:
            # Specify the version to avoid installing a newer version than intended.
            subprocess.run([pipFilePath, "install", f'{package["name"]}=={package["latest_version"]}'])

if isBeautifulSoup4OriginallyInstalled == False:
    subprocess.run([pipFilePath, "uninstall", "beautifulsoup4", "-y"])
