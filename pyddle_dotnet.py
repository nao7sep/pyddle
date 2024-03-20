# Created: 2024-03-06
# This script contains functions related to compilation and distribution of .NET projects.

import json
import os
import pyddle_file_system as file_system
import pyddle_path # path is a too common name.
import pyddle_string as string
import re
import shutil
import subprocess
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

    def archive(self, not_archived_directory_names=None, not_archived_file_names=None):
        return archive_solution(self, not_archived_directory_names, not_archived_file_names)

class ProjectInfo:
    def __init__(self, solutions, solution, name, directory_path, file_path):
        self.solutions = solutions
        self.solution = solution
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

    def build(self, no_restore=False):
        return build_project(self, no_restore)

    def update_nuget_packages(self):
        return update_nuget_packages_in_project(self)

    def rebuild_and_archive(self, supported_runtimes, not_archived_directory_names=None, not_archived_file_names=None):
        return rebuild_and_archive_project(self, supported_runtimes, not_archived_directory_names, not_archived_file_names)

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
#     loosely validate it, look for a referenced project matching the name and let it crash if the settings or the implementation require an update.

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
                    file_name_without_extension, _ = os.path.splitext(pyddle_path.basename(include))
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

def get_all_referenced_projects(project):
    referenced_projects = []

    for referenced_project in project.referenced_projects:
        if referenced_project not in referenced_projects:
            referenced_projects.append(referenced_project)

        referenced_projects.extend(get_all_referenced_projects(referenced_project))

    return referenced_projects

def sort_projects_to_build(projects):
    # A simple algorithm that assumes there's no cross-referencing issues between the projects.
    # As long as the number of the projects is small, it should perform just fine.

    # Extracts each project's referenced projects beforehand.
    reference_table = { project: get_all_referenced_projects(project) for project in projects }

    sorted_projects = []

    for project in projects:
        is_referenced = False

        for index, sorted_project in enumerate(sorted_projects):
            # Comparing against the extracted list.
            if project in reference_table[sorted_project]:
                sorted_projects.insert(index, project)
                is_referenced = True
                break

        if is_referenced == False:
            sorted_projects.append(project)

    return sorted_projects

# ------------------------------------------------------------------------------
#     Solution-related operations
# ------------------------------------------------------------------------------

def archive_solution(solution, not_archived_directory_names=None, not_archived_file_names=None):
    messages = []

    solution_archives_directory_path = pyddle_path.dirname(solution.source_archive_file_path)
    os.makedirs(solution_archives_directory_path, exist_ok=True)

    archived_file_count = file_system.zip_archive_directory(solution.directory_path, solution.source_archive_file_path, not_archived_directory_names, not_archived_file_names)

    if archived_file_count:
        messages.append(f"Archive file created: {solution.source_archive_file_path}")

    else:
        os.remove(solution.source_archive_file_path)
        messages.append(f"Empty archive file deleted: {solution.source_archive_file_path}")

    return messages

# ------------------------------------------------------------------------------
#     Project-related operations
# ------------------------------------------------------------------------------

def build_project(project, no_restore=False):
    # https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-build

    # "--nologo" isnt included so that we can log the version of the tool.
    # It should look like: MSBuild のバージョン 17.9.4+90725d08d (.NET)
    args = [ "dotnet", "build", project.file_path, "--configuration", "Release" ]

    if no_restore:
        args.append("--no-restore")

    result = subprocess.run(args, capture_output=True, cwd=project.directory_path)
    return subprocess_result_into_messages(result)

def update_nuget_packages_in_project(project):
    messages = []

    # https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-list-package

    args = [ "dotnet", "list", project.file_path, "package", "--outdated", "--format", "console" ] # Output for display.
    result = subprocess.run(args, capture_output=True, cwd=project.directory_path)
    messages.extend(subprocess_result_into_messages(result))

    args = [ "dotnet", "list", project.file_path, "package", "--outdated", "--format", "json" ] # For parsing.
    result = subprocess.run(args, capture_output=True, cwd=project.directory_path)

    # When an old project contains "package.config", which isnt supported by the "dotnet" command, we get a string like the following set to "stderr":
    #     プロジェクト 'C:\Repositories\Nekote2018\Nekote2018\Nekote2018.csproj' では NuGet パッケージに package.config を使用しますが、コマンドはパッケージ参照プロジェクトでのみ動作します。
    # But the JSON output, regardless of whether there's been an error or not, seems to have the same structure, allowing us to simply look for the "frameworks" key.

    # Added: 2024-03-20
    # After attempting to use MSBuild, older versions of it, the NuGet CLI, etc to anyhow update the packages of old projects,
    #     I ended up just migrating all the old projects from .NET Framework 4.8 to .NET 8 about a week ago.
    # Now everything is built and archived automatically.

    # We need to look for "projects/frameworks/topLevelPackages", which should be an array of dictionaries.
    # In each dictionary, we get "id", "requestedVersion", "resolvedVersion", "latestVersion".
    # Maybe oneday, we might need to utilize other tools to check compatibility.
    # For now, considering that a lot of issues can be resolved manually, we'll just attempt to update each package to the latest version suggested.

    json_string = result.stdout.decode("utf-8")
    data_from_json = json.loads(json_string)

    # Assuming the JSON structure is correct.
    # That is by design, hoping to find errors the implementation could miss otherwise.

    for project_in_json in data_from_json["projects"]:
        if "frameworks" in project_in_json:
            for framework in project_in_json["frameworks"]:
                if "topLevelPackages" in framework:
                    for package in framework["topLevelPackages"]:
                        id = package["id"]
                        latest_version = package["latestVersion"]

                        # https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-add-package

                        args = [ "dotnet", "add", project.file_path, "package", id, "--version", latest_version ]
                        result = subprocess.run(args, capture_output=True, cwd=project.directory_path)
                        messages.extend(subprocess_result_into_messages(result))

    return messages

# Originally planned to implement code analysis too, but I believe that would actually lower the productivity.

# By adding <AnalysisMode>AllEnabledByDefault</AnalysisMode> to the .csproj file, we can observe a lot more warnings on Visual Studio.
# The problem is that the analysis doesnt know what it's analyzing and so only coding-manner-related things come out.
# Like, "Use the async version instead", "Consider making this read-only", "Dont embed a literal string", "There's a newer way of writing this", etc.

# As far as I remember, the only (slightly) useful message I have ever got was a suggestion to use AsSpan instead of Substring.
# But code analysis anyway wouldnt tell us to use IndexOf rather than a for/foreach loop when that could drastically improve the performance.

# Soon, AI will start refactoring large portions of code, changing the design completely.
# Until then, although we cant say there's absolutely no merit in code analysis, it doesnt need to be a part of everyday development.

def rebuild_and_archive_project(project, supported_runtimes, not_archived_directory_names=None, not_archived_file_names=None):
    messages = []

    # For testing purposes only.
    # When I wasnt sure what I was doing with "dotnet build --no-incremental" and "dotnet publish --no-build" due to the issues described below,
    #     I had to make sure I wasnt unintentionally linking old binaries of class libraries to newly built apps.

    vs_directory_path = os.path.join(project.solution.directory_path, ".vs")
    # shutil.rmtree(vs_directory_path, ignore_errors=True)

    bin_directory_path = os.path.join(project.directory_path, "bin")
    # shutil.rmtree(bin_directory_path, ignore_errors=True)

    obj_directory_path = os.path.join(project.directory_path, "obj")
    # shutil.rmtree(obj_directory_path, ignore_errors=True)

    # "dotnet publish", when a runtime is specified by the "--runtime" option, internally runs "dotnet build --runtime",
    #     which seems to generate platform-agonistic binaries (or something that can be turned into them)
    #     somewhere in the obj directory and platform-specific ones in the bin directory.
    # When I deleted the bin and obj directories of a project with no references and ran this script,
    #     binaries were output ONLY to bin/Release/net8.0/win-x64 and NOT bin/Release or bin/Release/net8.0.

    # When the files were messy and the code was unstable, my understanding was more like:
    #     * "dotnet publish --runtime" internally calls "dotnet build" without a runtime specified
    #     * Platform-agonistic binaries are generated to bin/Release/net8.0 by the runtime-unspecified "dotnet build"
    #     * Platform-specific binaries are generated to bin/Release/net8.0/win-x64 by the runtime-specified "dotnet publish --runtime"

    # Now I believe it's more like:
    #     * "dotnet publish --runtime" internally calls "dotnet build --runtime" with a runtime specified
    #     * Platform-agonistic binaries are generated somewhere in the obj directory by the runtime-specified "dotnet build --runtime"
    #     * Platform-specific binaries are generated to bin/Release/net8.0/win-x64 by the runtime-specified "dotnet build --runtime"
    #     * So, all the binaries are generated by the runtime-specified "dotnet build --runtime"
    #     * "dotnet publish --runtime" just copies whatever needed, possibly updating metadata and adjusting the binaries for the runtime

    # Currently, yyTodoMail references yyLib.
    # When I rebuilt and archived them with this script, I got 2 archives.
    # Let's call them yyTodoMail.zip and yyLib.zip here.

    # What I wasnt expecting was:
    #     * yyLib.dll in yyTodoMail.zip was different from yyLib.dll in yyLib.zip
    #     * yyLib.dll in yyTodoMail.zip was the same as the platform-agonistic one in yyLib/bin/Release/net8.0
    #     * yyLib.dll in yyLib.zip was the same as the platform-specific one in yyLib/bin/Release/net8.0/win-x64

    # ChatGPT and other sources say that recent .NET binaries, especially those of class libraries, are generally platform-agonistic.
    # People say different things most likely because .NET used to be a Windows-only thing and so much has changed since then.
    # I believe now it's safe to say .NET has become like Java, where the binaries are platform-agonistic by default.
    # Well, at least non-executable DLL files should be.

    # For this reason, "dotnet publish --runtime" with a runtime specified selected the platform-agonistic binaries of yyLib for yyTodoMail,
    #     NOT the platform-specific ones matching the runtime specified to the command, and archived them into yyTodoMail.zip.
    # Then, this script, following its design, archived the platform-specific binaries of yyLib into yyLib.zip.

    # Actually, there's not much point in distributing platform-specific binaries of class libraries
    #     especially when their source code is available and they are easy to build.
    # If yyLib was like a hundred times larger and more complicated to build,
    #     distributing platform-specific binaries for all major platforms would be meaningful, though.

    # Now about RE-building:
    # "dotnet clean" deletes files in the bin and obj directories that have been generated by "dotnet build".
    # ChatGPT said it's a platform-agnostic operation and, even when "dotnet publish --runtime" with a runtime specified had been run,
    #     we didnt necessarily have to specify the runtime to "dotnet clean".
    # That seemed incorrect.
    # When I followed the advice, "dotnet publish --runtime" didnt update the binaries.
    # In the archives, unless the source code had been changed, I always got old binaries with old timestamps.

    # After some testing, I believe:
    #     * "dotnet clean" too chooses what part of the project to clean based on the runtime specified
    #     * If we want to rebuild a project for a specific platform, we need to run "dotnet clean --runtime" for that platform
    #     * We need "dotnet clean" without a runtime specified ONLY if we want to rebuild the platform-agonistic binaries

    # This script runs "dotnet build" without a runtime specified for "1) Build"
    #     and "dotnet publish --runtime" with a runtime specified for "3) Rebuild and archive".
    # #1 is for repeated testing and, therefore, should be fast by utilizing the incremental build feature.
    # #3 is for releasing and, therefore, should rebuild everything and set the current timestamps to the binaries.

    # Some say we should just delete the bin and obj directories considering that's the simplest way.
    # I like it's simplicity, but I prefer not to do this because various runtime-generated test files too will be deleted.

    # Some others say "dotnet build --no-incremental" followed by "dotnet publish --no-build" is the right way.
    # As .NET's build system is complex, I prefer to avoid expecting the "--no-incremental" option to work perfectly
    #     especially when a script like this attempts to build more than 10 projects at once.
    # Sometimes, some outdated/redundant files may be left in the bin and obj directories.
    # If there's a command that's supposed to clean things without affecting test files, let's simply use it. :)

    # The algorithm in this script seems to properly sort the projects in a way that the referenced projects are built first
    #     as long as there's no cross-referencing issues between the projects.
    # The best practice so far is:
    #     * "dotnet build" without a runtime specified or running "dotnet clean" beforehand for fast incremental builds to be tested
    #     * "dotnet clean --runtime" followed by "dotnet publish --runtime" for platform-specific binaries to be distributed

    # https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-clean
    # https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-publish

    for supported_runtime in supported_runtimes:
        runtime_specific_publish_directory_path = os.path.join(project.directory_path, "bin", "Publish", supported_runtime)

        if os.path.isdir(runtime_specific_publish_directory_path):
            shutil.rmtree(runtime_specific_publish_directory_path)

        args = [ "dotnet", "clean", project.file_path, "--configuration", "Release", "--runtime", supported_runtime ]
        result = subprocess.run(args, capture_output=True, cwd=project.directory_path)
        result.stdout = None # We dont need to see the list of files deleted.
        messages.extend(subprocess_result_into_messages(result))

        args = [ "dotnet", "publish", project.file_path, "--configuration", "Release", "--output", runtime_specific_publish_directory_path, "--runtime", supported_runtime ]
        result = subprocess.run(args, capture_output=True, cwd=project.directory_path)
        messages.extend(subprocess_result_into_messages(result))

        solution_archives_directory_path = pyddle_path.dirname(project.solution.source_archive_file_path)
        os.makedirs(solution_archives_directory_path, exist_ok=True)

        binaries_archive_file_name = f"{project.name}-v{project.version_string}-{supported_runtime}.zip"
        binaries_archive_file_path = os.path.join(solution_archives_directory_path, binaries_archive_file_name)
        archived_file_count = file_system.zip_archive_directory(runtime_specific_publish_directory_path, binaries_archive_file_path, not_archived_directory_names, not_archived_file_names)

        if archived_file_count:
            messages.append(f"Archive file created: {binaries_archive_file_path}")

        else:
            os.remove(binaries_archive_file_path)
            messages.append(f"Empty archive file deleted: {binaries_archive_file_path}")

    return messages

# ------------------------------------------------------------------------------
#     Misc
# ------------------------------------------------------------------------------

def subprocess_result_into_messages(result):
    messages = []

    if result.stdout:
        messages.append("stdout:")
        messages.extend(f'{string.leveledIndents[1]}{message}' for message in result.stdout.decode("utf-8").splitlines() if message)

    if result.stderr:
        messages.append("stderr:")
        messages.extend(f'{string.leveledIndents[1]}{message}' for message in result.stderr.decode("utf-8").splitlines() if message)

    return messages

def format_result_string_from_messages(messages, indents="", end="\n"):
    return end.join(f"{indents}{message}" for message in messages)
