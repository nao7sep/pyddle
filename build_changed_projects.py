import glob
import os
import pyddle_debugging as debugging
import pyddle_dotnet as dotnet
import pyddle_json_based_kvs as kvs
import pyddle_string as string
import sys
import traceback

try:
    # ------------------------------------------------------------------------------
    #     Load settings
    # ------------------------------------------------------------------------------

    kvs_key_prefix = "build_changed_projects/"

    repositories_directory_path = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}repositories_directory_path")
    print(f"repositories_directory_path: {repositories_directory_path}")

    archives_directory_path = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}archives_directory_path")
    print(f"archives_directory_path: {archives_directory_path}")

    # A neutral character that is rarely used in solution/project names.
    value_separator = "|"

    ignored_directory_names = []
    ignored_directory_names_string = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}ignored_directory_names")

    if ignored_directory_names_string:
        ignored_directory_names = [value.strip() for value in ignored_directory_names_string.split(value_separator) if value.strip()]

        if ignored_directory_names:
            print(f"ignored_directory_names: {ignored_directory_names}")

    obsolete_solution_names = []
    obsolete_solution_names_string = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}obsolete_solution_names")

    if obsolete_solution_names_string:
        obsolete_solution_names = [value.strip() for value in obsolete_solution_names_string.split(value_separator) if value.strip()]

        if obsolete_solution_names:
            print(f"obsolete_solution_names: {obsolete_solution_names}")

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
                print(f"Ignored directory: {directory_name}")

            continue

        solution_file_paths = glob.glob(os.path.join(possible_solution_directory_path, "*.sln"))

        if not solution_file_paths:
            if debugging.is_debugging():
                print(f"No solution files found in directory: {directory_name}")

            continue

        # Set the full path for now.
        solution_directories[directory_name] = possible_solution_directory_path

    if not solution_directories:
        print("No solution directories found.")
        # "sys.exit" raises a "SystemExit" exception, which is NOT caught by the "except" block if a type is specified, allowing the script to execute the "finally" block.
        # "exit", on the other hand, is merely a helper for the interactive shell and should not be used in production code.
        sys.exit()

    # ------------------------------------------------------------------------------
    #     Find project directories
    # ------------------------------------------------------------------------------

    for solution_name, solution_directory_path in solution_directories.items():
        project_directories = {}

        for directory_name in os.listdir(solution_directory_path):
            possible_project_directory_path = os.path.join(solution_directory_path, directory_name)

            if not os.path.isdir(possible_project_directory_path):
                continue

            # It's highly unlikely that a known better-to-avoid name (such as ".git") is used as a valid solution/project directory name.
            if string.contains_ignore_case(ignored_directory_names, directory_name):
                if debugging.is_debugging():
                    print(f"Ignored directory: {solution_name}/{directory_name}")

                continue

            project_file_paths = glob.glob(os.path.join(possible_project_directory_path, "*.csproj"))

            if not project_file_paths:
                if debugging.is_debugging():
                    print(f"No project files found in directory: {solution_name}/{directory_name}")

                continue

            project_directories[directory_name] = possible_project_directory_path

        if not project_directories:
            print(f"No project directories found in solution: {solution_name}")
            continue

        solution_directories[solution_name] = solution_directory_path, project_directories

# If we dont specify the exception type, things such as KeyboardInterrupt and SystemExit too may be caught.
except Exception:
    traceback.print_exc()

finally:
    debugging.display_press_enter_key_to_continue_if_not_debugging()
