# Created: 2024-03-06
# This script contains functions related to compilation and distribution of .NET projects.

import os
import pyddle_debugging as debugging
import pyddle_file_system as file_system
import pyddle_string as string
import re
import xml.etree.ElementTree

# ------------------------------------------------------------------------------
#     Solution/project info
# ------------------------------------------------------------------------------

# I wont be implementing the searching-for-things part in this module
#     because it would need to output various messages and also MIGHT become interactive in the future.
# For this reason, "projects" is set from the outside.

class SolutionInfo:
    def __init__(self, solutions, archives_directory_path, name, directory_path, file_path, is_obsolete):
        self.solutions = solutions
        self.archives_directory_path = archives_directory_path
        self.name = name
        self.directory_path = directory_path
        self.file_path = file_path
        self.is_obsolete = is_obsolete
        self.projects = None
        self.__common_version_string = None
        self.__source_archive_file_path = None

    @property
    def common_version_string(self):
        if self.__common_version_string is None:
            # Should exist.
            first_version_string = self.projects[0].version_string

            for project in self.projects[1:]:
                if not string.equals(project.version_string, first_version_string):
                    raise RuntimeError(f"Version strings differ.")

            self.__common_version_string = first_version_string

        return self.__common_version_string

    @property
    def source_archive_file_path(self):
        if self.__source_archive_file_path is None:

            source_archive_file_name = f"{self.name}-v{self.common_version_string}-src.zip"

            if self.is_obsolete:
                # The directory already exists and its name starts with a capital letter.
                self.__source_archive_file_path = os.path.join(self.archives_directory_path, "Obsolete", self.name, source_archive_file_name)

            else:
                self.__source_archive_file_path = os.path.join(self.archives_directory_path, self.name, source_archive_file_name)

        return self.__source_archive_file_path

class ProjectInfo:
    def __init__(self, solutions, name, directory_path, file_path):
        self.solutions = solutions
        self.name = name
        self.directory_path = directory_path
        self.file_path = file_path
        self.__version_string = None
        self.__referenced_projects = None

    @property
    def version_string(self):
        if self.__version_string is None:
            extracted_version_string = extract_version_string_from_csproj_file(self.file_path)

            if extracted_version_string:
                try:
                    extracted_version_string = version_digits_to_string(parse_version_string(extracted_version_string))

                except Exception:
                    raise RuntimeError(f"Invalid version string: {extracted_version_string}")

                app_manifest_file_path = os.path.join(self.directory_path, "app.manifest")

                if os.path.isfile(app_manifest_file_path):
                    alternatively_extracted_version_string = extract_version_string_from_app_manifest_file(app_manifest_file_path)

                    if alternatively_extracted_version_string:
                        try:
                            alternatively_extracted_version_string = version_digits_to_string(parse_version_string(alternatively_extracted_version_string))

                        except Exception:
                            raise RuntimeError(f"Invalid version string: {alternatively_extracted_version_string}")

                        if not string.equals(alternatively_extracted_version_string, extracted_version_string):
                            raise RuntimeError(f"Version strings from 2 files differ.")

                self.__version_string = extracted_version_string

            else:
                assembly_info_file_path = os.path.join(self.directory_path, "Properties", "AssemblyInfo.cs")

                if os.path.isfile(assembly_info_file_path):
                    extracted_version_string = extract_version_string_from_assembly_info_file(assembly_info_file_path)

                    if extracted_version_string:
                        # As the version string is extracted with a regex, it should be valid.
                        try:
                            self.__version_string = version_digits_to_string(parse_version_string(extracted_version_string))

                        except Exception:
                            raise RuntimeError(f"Invalid version string: {extracted_version_string}")

            if self.__version_string is None:
                raise RuntimeError(f"Version string not extracted.")

        return self.__version_string

    @property
    def referenced_projects(self):
        if self.__referenced_projects is None:
            extracted_referenced_project_names = extract_referenced_project_names_from_csproj_file(self.file_path)

            if extracted_referenced_project_names:
                referenced_projects = []

                for referenced_project_name in extracted_referenced_project_names:
                    referenced_project = find_referenced_project(self.solutions, referenced_project_name)

                    if not referenced_project:
                        raise RuntimeError(f"Referenced project not found: {referenced_project_name}")

                    referenced_projects.append(referenced_project)

                self.__referenced_projects = referenced_projects

            else:
                self.__referenced_projects = []

        return self.__referenced_projects

# ------------------------------------------------------------------------------
#     Version strings
# ------------------------------------------------------------------------------

def extract_version_string_from_csproj_file(path):
    """ Returns None if the version string is not found. """
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

def extract_default_namespace_from_root_tag(tag):
    """ Returns None if the default namespace is not found. """
    if tag.startswith("{"):
        return { "": tag[1 : tag.index("}")] }

def extract_version_string_from_app_manifest_file(path):
    """ Returns None if the version string is not found. """
    with file_system.open_file_and_detect_utf_encoding(path) as file:
        tree = xml.etree.ElementTree.parse(file)
        root = tree.getroot() # assembly
        namespaces = extract_default_namespace_from_root_tag(root.tag)

        assembly_identity = root.find("assemblyIdentity", namespaces=namespaces)

        if assembly_identity is not None:
            # https://docs.python.org/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element.get
            return assembly_identity.get("version")

assembly_info_file_version_string_pattern = r"\[assembly:\s*AssemblyVersion\s*\(\"(?P<version>\d+\.\d+(\.\d+){0,2})\"\)\]"

def extract_version_string_from_assembly_info_file(path):
    """
        Returns None if the version string is not found.
        As this method uses a regex, if a version string is extracted, it should be valid.
        There's no point in loosening the regex to match invalid version strings.
    """
    with file_system.open_file_and_detect_utf_encoding(path) as file:
        for line in file:
            if line.lstrip().startswith("//"):
                continue

            match = re.match(assembly_info_file_version_string_pattern, line)

            if match:
                return match.group("version")

def parse_version_string(str):
    """
        Returns a list of 4 integers.
        Raises a ValueError if the string is not a valid version string.
    """
    # https://learn.microsoft.com/en-us/dotnet/api/system.version.parse

    digits = [0, 0, 0, 0]
    parts = str.split(".")

    for index in range(len(parts)):
        # It's not clearly documented, but "int" seems to raise a ValueError if the string is not a number.
        # https://docs.python.org/3/library/functions.html#int
        digits[index] = int(parts[index])

    return digits

def version_digits_to_string(digits, minimum_digit_count=2):
    """
        Can be used to normalize a version string.
        Takes a list of 4 integers.
    """
    # "range" generates from 3 to 0.
    # Even if "digits" are all 0, "index" doesnt seem to be -1.
    for index in range(len(digits) - 1, -1, -1):
        if digits[index] > 0:
            break

    meaningful_digit_count = max(minimum_digit_count, index + 1)

    return ".".join(str(digit) for digit in digits[:meaningful_digit_count])

# ------------------------------------------------------------------------------
#     References
# ------------------------------------------------------------------------------

# We cant guarantee that this method will always find all references.
# Although .csproj files have been greatly simplified in .NET Core, we never know what will be added in the future.

# The fundamental approach, then, is to read the default namespace if it's in the root tag, read whatever that could be a reference,
#     loosely validate it, look for a referenced project matching the name and let it crush if the settings or the implementation require an update.

def extract_referenced_project_names_from_csproj_file(path):
    """ Returns an empty list if no references are found. """
    with file_system.open_file_and_detect_utf_encoding(path) as file:
        tree = xml.etree.ElementTree.parse(file)
        root = tree.getroot() # Project
        namespaces = extract_default_namespace_from_root_tag(root.tag)

        referenced_project_names = []

        for item_group in root.findall("ItemGroup", namespaces=namespaces):
            for project_reference in item_group.findall("ProjectReference", namespaces=namespaces):
                include = project_reference.get("Include")

                if include:
                    # It's usually like: <ProjectReference Include="..\yyLib\yyLib.csproj" />
                    file_name_without_extension, _ = os.path.splitext(os.path.basename(include))
                    referenced_project_names.append(file_name_without_extension)

            for reference in item_group.findall("Reference", namespaces=namespaces):
                include = reference.get("Include")

                if include:
                    # This one can be like:
                    #     <Reference Include="System" />
                    #     <Reference Include="System.ValueTuple, Version=4.0.3.0, Culture=neutral, PublicKeyToken=cc7b13ffcd2ddd51, processorArchitecture=MSIL"> ...
                    #     <Reference Include="yyLib"> ...

                    if is_valid_referenced_project_name(include):
                        referenced_project_names.append(include)

        return referenced_project_names

def is_valid_referenced_project_name(str):
    if '=' in str:
        return False

    # We must keep updating the following part.
    # Fortunately, since .NET Core, .csproj files contain only what's absolutely necessary.

    if string.equals_ignore_case(str, "System"):
        return False

    if string.startswith_ignore_case(str, "System."):
        return False

    if string.equals_ignore_case(str, "PresentationCore"):
        return False

    if string.equals_ignore_case(str, "WindowsBase"):
        return False

    if string.startswith_ignore_case(str, "Microsoft."):
        return False

    return True

def find_referenced_project(solutions, referenced_project_name):
    for solution in solutions:
        for project in solution.projects:
            if string.equals_ignore_case(project.name, referenced_project_name):
                return project
