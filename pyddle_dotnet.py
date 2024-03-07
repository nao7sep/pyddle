# Created: 2024-03-06
# This script contains functions related to compilation and distribution of .NET projects.

import os
import pyddle_console as console
import pyddle_debugging as debugging
import pyddle_file_system as file_system
import pyddle_string as string
import re
import xml.etree.ElementTree

# ------------------------------------------------------------------------------
#     Solution/project info
# ------------------------------------------------------------------------------

# I wont be implementing the searching-for-things part in this module because it would need to output various messages and also MIGHT become interactive in the future.

class SolutionInfo:
    def __init__(self, directory_path, file_path, projects=None):
        self.directory_path = directory_path
        self.file_path = file_path
        self.projects = projects

class ProjectInfo:
    def __init__(self, directory_path, file_path, version_string=None):
        self.directory_path = directory_path
        self.file_path = file_path
        self.version_string = version_string

    # This could be a property with the @property thing attached, but currently there seems to be no built-in Lazy mechanism in Python,
    #    and I dont want the property-ish thing to try to initialize itself multiple times if it cant extract the version string.

    def extract_and_normalize_version_string(self):
        if self.version_string:
            raise RuntimeError("Version string already exists.")

        try:
            extracted_version_string = extract_version_string_from_csproj_file(self.file_path)

            if extracted_version_string:
                extracted_version_string = version_digits_to_string(parse_version_string(extracted_version_string))

                # Avalonia UI may contain a version string in "app.manifest" that should, but not necessarily have to, match the one in the .csproj file.
                # If the file exists and contains a version string, why dont we just check it?
                # The check occurs only in the debugging mode because I dont like it directly displaying a warning message (while I'm too lazy to do better).

                if debugging.is_debugging():
                    app_manifest_file_path = os.path.join(self.directory_path, "app.manifest")

                    if os.path.isfile(app_manifest_file_path):
                        alternatively_extracted_version_string = extract_version_string_from_app_manifest_file(app_manifest_file_path)

                        if alternatively_extracted_version_string:
                            alternatively_extracted_version_string = version_digits_to_string(parse_version_string(alternatively_extracted_version_string))

                            if not string.equals(alternatively_extracted_version_string, extracted_version_string):
                                console.print_warning(f"Version strings from '{os.path.basename(self.file_path)}' and 'app.manifest' differ in directory: {self.directory_path}")
                                return False

                        # If the file exists and doesnt contain a version string,
                        #     it's probably a different kind of "app.manifest" and it's not a problem.

                self.version_string = extracted_version_string

                return True

            # Old .NET projects may contain a version string in "AssemblyInfo.cs".
            # I used to set the same value to AssemblyVersion and AssemblyFileVersion,
            #     but I wont be checking the latter because all my old .NET projects are deprecated.

            assembly_info_file_path = os.path.join(self.directory_path, "Properties", "AssemblyInfo.cs")

            if os.path.isfile(assembly_info_file_path):
                extracted_version_string = extract_version_string_from_assembly_info_file(assembly_info_file_path)

                if extracted_version_string:
                    self.version_string = version_digits_to_string(parse_version_string(extracted_version_string))
                    return True

        except Exception:
            return False

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
