import pyddle_first as first

first.set_main_script_file_path(__file__)

import glob
import os
import pyddle_debugging as debugging
import pyddle_dotnet as dotnet
import pyddle_json_based_kvs as kvs
import pyddle_logging as logging
import pyddle_output as output
import pyddle_string as string
import sys
import traceback

try:
    # ------------------------------------------------------------------------------
    #     Load settings
    # ------------------------------------------------------------------------------

    kvs_key_prefix = "build_changed_projects/"

    repositories_directory_path = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}repositories_directory_path")
    output.print_and_log(f"repositories_directory_path: {repositories_directory_path}")

    archives_directory_path = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}archives_directory_path")
    output.print_and_log(f"archives_directory_path: {archives_directory_path}")

    # A neutral character that is rarely used in solution/project names.
    value_separator = "|"

    ignored_directory_names = []
    ignored_directory_names_string = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}ignored_directory_names")

    if ignored_directory_names_string:
        ignored_directory_names = [value.strip() for value in ignored_directory_names_string.split(value_separator) if value.strip()]

        if ignored_directory_names:
            output.print_and_log(f"ignored_directory_names: {ignored_directory_names}")

    obsolete_solution_names = []
    obsolete_solution_names_string = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}obsolete_solution_names")

    if obsolete_solution_names_string:
        obsolete_solution_names = [value.strip() for value in obsolete_solution_names_string.split(value_separator) if value.strip()]

        if obsolete_solution_names:
            output.print_and_log(f"obsolete_solution_names: {obsolete_solution_names}")

    # ------------------------------------------------------------------------------
    #     Find solution directories
    # ------------------------------------------------------------------------------

    solution_directories = {}

    # "os.listdir" returns not only directories but also files.
    # https://www.geeksforgeeks.org/python-os-listdir-method/
    for directory_name in os.listdir(repositories_directory_path):
        possible_solution_directory_path = os.path.join(repositories_directory_path, directory_name)

        if not os.path.isdir(possible_solution_directory_path):
            continue

        if string.contains_ignore_case(ignored_directory_names, directory_name):
            if debugging.is_debugging():
                output.print_and_log(f"Ignored directory: {directory_name}")

            continue

        solution_file_paths = glob.glob(os.path.join(possible_solution_directory_path, "*.sln"))

        if not solution_file_paths:
            if debugging.is_debugging():
                output.print_and_log_warning(f"No solution files found in directory: {directory_name}")

            continue

        if len(solution_file_paths) > 1:
            output.print_and_log_warning(f"Multiple solution files found in directory: {directory_name}")
            continue

        solution_directories[directory_name] = dotnet.SolutionInfo(directory_name, possible_solution_directory_path, solution_file_paths[0])

    if not solution_directories:
        output.print_and_log_warning(f"No solution directories found.")
        # "sys.exit" raises a "SystemExit" exception, which is NOT caught by the "except" block if a type is specified, allowing the script to execute the "finally" block.
        # "exit", on the other hand, is merely a helper for the interactive shell and should not be used in production code.
        sys.exit()

    # ------------------------------------------------------------------------------
    #     Find project directories
    # ------------------------------------------------------------------------------

    for solution_name, solution in solution_directories.items():
        project_directories = {}

        for directory_name in os.listdir(solution.directory_path):
            possible_project_directory_path = os.path.join(solution.directory_path, directory_name)

            if not os.path.isdir(possible_project_directory_path):
                continue

            # It's highly unlikely that a known better-to-avoid name (such as ".git") is used as a valid solution/project directory name.
            if string.contains_ignore_case(ignored_directory_names, directory_name):
                if debugging.is_debugging():
                    output.print_and_log(f"Ignored directory: {solution_name}/{directory_name}")

                continue

            project_file_paths = glob.glob(os.path.join(possible_project_directory_path, "*.csproj"))

            if not project_file_paths:
                if debugging.is_debugging():
                    output.print_and_log_warning(f"No project files found in directory: {solution_name}/{directory_name}")

                continue

            if len(project_file_paths) > 1:
                output.print_and_log_warning(f"Multiple project files found in directory: {solution_name}/{directory_name}")
                continue

            project_directories[directory_name] = dotnet.ProjectInfo(directory_name, possible_project_directory_path, project_file_paths[0])

        if not project_directories:
            output.print_and_log_warning(f"No project directories found in solution: {solution_name}")
            continue

        solution_directories[solution_name].projects = project_directories

    # ------------------------------------------------------------------------------
    #     Read version strings, references, etc
    # ------------------------------------------------------------------------------

    valid_project_count = 0

    for solution_name, solution in sorted(solution_directories.items()):
        for project_name, project in sorted(solution.projects.items()):
            result, message = project.extract_and_normalize_version_string()

            if result: # Has a valid version string.
                output.print_and_log(f"{solution_name}/{project_name}: {project.version_string}")

                result, message = project.extract_referenced_project_names_and_find_them(solution_directories)

                if result: # All referenced projects are found or there are no references.
                    if project.referenced_projects:
                        for referenced_project in sorted(project.referenced_projects, key=lambda x: x.name):
                            output.print_and_log(f"{referenced_project.name}{referenced_project.version_string}", indent="    ")

                    else:
                        # Displays the message that there are no references.
                        output.print_and_log(message, indent="    ")

                    valid_project_count += 1

                else: # At least one of the referenced projects is not found.
                    output.print_and_log_error(message, indent="    ")

            else: # Doesnt have a valid version string.
                # Indentation not required here.
                output.print_and_log_error(f"{solution_name}/{project_name}: {message}")

    if valid_project_count:
        output.print_and_log(f"{valid_project_count} valid projects found.")

    else:
        output.print_and_log_warning("No valid projects found.")
        sys.exit()

# If we dont specify the exception type, things such as KeyboardInterrupt and SystemExit too may be caught.
except Exception:
    traceback.print_exc()

finally:
    logging.flush()
    debugging.display_press_enter_key_to_continue_if_not_debugging()
