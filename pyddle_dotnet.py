# Created: 2024-03-06
# This script contains functions related to compilation and distribution of .NET projects.

import enum
import pyddle_file_system as file_system
import re
import xml.etree.ElementTree

# ------------------------------------------------------------------------------
#     Version strings
# ------------------------------------------------------------------------------

def extract_version_string_from_csproj_file(path):
    with file_system.open_file_and_detect_utf_encoding(path) as file:
        tree = xml.etree.ElementTree.parse(file)
        root = tree.getroot() # Project

        # https://docs.python.org/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element.find
        property_group = root.find("PropertyGroup")

        if property_group is not None:
            version = property_group.find("Version")

            # The Version element, with no child elements, can be considered falsy.
            # "if version:" doesnt seem to work.
            # If it's not None, it should contain a string.
            if version is not None:
                return version.text

def extract_version_string_from_app_manifest_file(path):
    with file_system.open_file_and_detect_utf_encoding(path) as file:
        tree = xml.etree.ElementTree.parse(file)
        root = tree.getroot() # assembly

        assembly_identity = root.find("{urn:schemas-microsoft-com:asm.v1}assemblyIdentity")

        if assembly_identity is not None:
            # https://docs.python.org/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element.get
            return assembly_identity.get("version")

assembly_info_file_s_version_string_pattern = r"\[assembly:\s*AssemblyVersion\s*\(\"(?P<version>\d+\.\d+(\.\d+){0,2})\"\)\]"

def extract_version_string_from_assembly_info_file(path):
    with file_system.open_file_and_detect_utf_encoding(path) as file:
        for line in file:
            if line.lstrip().startswith("//"):
                continue

            match = re.match(assembly_info_file_s_version_string_pattern, line)

            if match:
                return match.group("version")

def parse_version_string(str):
    # https://learn.microsoft.com/en-us/dotnet/api/system.version.parse

    digits = [0, 0, 0, 0]
    parts = str.split(".")

    for index in range(len(parts)):
        # It's not clearly documented, but "int" seems to raise a ValueError if the string is not a number.
        # https://docs.python.org/3/library/functions.html#int
        digits[index] = int(parts[index])

    return digits

def version_digits_to_string(digits, minimum_digit_count=2):
    # "range" generates from 3 to 0.
    # Even if "digits" are all 0, "index" doesnt seem to be -1.
    for index in range(len(digits) - 1, -1, -1):
        if digits[index] > 0:
            break

    meaningful_digit_count = max(minimum_digit_count, index + 1)

    return ".".join(str(digit) for digit in digits[:meaningful_digit_count])

class VersionStringContainingFileType(enum.Enum):
    CSPROJ = 1
    APP_MANIFEST = 2
    ASSEMBLY_INFO = 3

def extract_and_normalize_version_string_from_file(path, type, minimum_digit_count=2):
    extracted_string = ""

    if type == VersionStringContainingFileType.CSPROJ:
        extracted_string = extract_version_string_from_csproj_file(path)
    elif type == VersionStringContainingFileType.APP_MANIFEST:
        extracted_string = extract_version_string_from_app_manifest_file(path)
    elif type == VersionStringContainingFileType.ASSEMBLY_INFO:
        extracted_string = extract_version_string_from_assembly_info_file(path)

    # If the file doesnt contain a valid version string, an exception must be raised.
    return version_digits_to_string(parse_version_string(extracted_string), minimum_digit_count)
