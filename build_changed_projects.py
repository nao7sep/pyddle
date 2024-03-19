# Created: 2024-03-11
# This script builds and archives all changed projects in the specified repositories directory.

import pyddle_first as first

first.set_main_script_file_path(__file__)

import glob
import os
import pyddle_console as console
import pyddle_debugging as debugging
import pyddle_dotnet as dotnet
import pyddle_json_based_kvs as kvs
import pyddle_logging as logging
import pyddle_output as output
import pyddle_string as string
import random
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

    supported_runtimes = []
    supported_runtimes_string = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}supported_runtimes")

    if supported_runtimes_string:
        supported_runtimes = [value.strip() for value in supported_runtimes_string.split(value_separator) if value.strip()]

        if supported_runtimes:
            output.print_and_log(f"supported_runtimes: {supported_runtimes}")

    not_archived_directory_names = []
    not_archived_directory_names_string = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}not_archived_directory_names")

    if not_archived_directory_names_string:
        not_archived_directory_names = [value.strip() for value in not_archived_directory_names_string.split(value_separator) if value.strip()]

        if not_archived_directory_names:
            output.print_and_log(f"not_archived_directory_names: {not_archived_directory_names}")

    not_archived_file_names = []
    not_archived_file_names_string = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}not_archived_file_names")

    if not_archived_file_names_string:
        not_archived_file_names = [value.strip() for value in not_archived_file_names_string.split(value_separator) if value.strip()]

        if not_archived_file_names:
            output.print_and_log(f"not_archived_file_names: {not_archived_file_names}")

    # ------------------------------------------------------------------------------
    #     Find solution directories
    # ------------------------------------------------------------------------------

    solutions = []

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

        is_obsolete_solution = string.contains_ignore_case(obsolete_solution_names, directory_name)
        solutions.append(dotnet.SolutionInfo(solutions, archives_directory_path, directory_name, possible_solution_directory_path, solution_file_paths[0], is_obsolete_solution))

    if not solutions:
        output.print_and_log_warning(f"No solution directories found.")
        # "sys.exit" raises a "SystemExit" exception, which is NOT caught by the "except" block if a type is specified, allowing the script to execute the "finally" block.
        # "exit", on the other hand, is merely a helper for the interactive shell and should not be used in production code.
        sys.exit()

    # ------------------------------------------------------------------------------
    #     Find project directories
    # ------------------------------------------------------------------------------

    for solution in solutions:
        project_directories = []

        for directory_name in os.listdir(solution.directory_path):
            possible_project_directory_path = os.path.join(solution.directory_path, directory_name)

            if not os.path.isdir(possible_project_directory_path):
                continue

            # It's highly unlikely that a known better-to-avoid name (such as ".git") is used as a valid solution/project directory name.
            if string.contains_ignore_case(ignored_directory_names, directory_name):
                if debugging.is_debugging():
                    output.print_and_log(f"Ignored directory: {solution.name}/{directory_name}")

                continue

            project_file_paths = glob.glob(os.path.join(possible_project_directory_path, "*.csproj"))

            if not project_file_paths:
                if debugging.is_debugging():
                    output.print_and_log_warning(f"No project files found in directory: {solution.name}/{directory_name}")

                continue

            if len(project_file_paths) > 1:
                output.print_and_log_warning(f"Multiple project files found in directory: {solution.name}/{directory_name}")
                continue

            project_directories.append(dotnet.ProjectInfo(solutions, solution, directory_name, possible_project_directory_path, project_file_paths[0]))

        if not project_directories:
            output.print_and_log_warning(f"No project directories found in solution: {solution.name}")
            continue

        solution.projects = project_directories

    # ------------------------------------------------------------------------------
    #     Read version strings, references, etc
    # ------------------------------------------------------------------------------

    valid_project_count = 0

    for solution in sorted(solutions, key=lambda x: x.name):
        try:
            output.print_and_log(f"{solution.name} v{solution.common_version_string}")

            if not os.path.isfile(solution.source_archive_file_path):
                output.print_and_log_important(solution.source_archive_file_path, indents=string.leveledIndents[1])

            for project in sorted(solution.projects, key=lambda x: x.name):
                try:
                    output.print_and_log(f"{project.name} v{project.version_string}", indents=string.leveledIndents[1])

                    try:
                        if project.referenced_projects:
                            for referenced_project in sorted(project.referenced_projects, key=lambda x: x.name):
                                output.print_and_log(f"{referenced_project.name} v{referenced_project.version_string}", indents=string.leveledIndents[2])

                        else:
                            output.print_and_log(f"No referenced projects found.", indents=string.leveledIndents[2])

                        valid_project_count += 1

                    except Exception as exception:
                        # Looks prettier without the project name.
                        output.print_and_log_error(f"{exception}", indents=string.leveledIndents[2])

                except Exception as exception:
                    output.print_and_log_error(f"{project.name}: {exception}", indents=string.leveledIndents[1])

        except Exception as exception:
            output.print_and_log_error(f"{solution.name}: {exception}")

    if valid_project_count:
        output.print_and_log(f"{valid_project_count} valid projects found.")

    else:
        output.print_and_log_warning("No valid projects found.")
        sys.exit()

    # ------------------------------------------------------------------------------
    #     Main loop
    # ------------------------------------------------------------------------------

    projects_to_build = []

    for solution in solutions:
        if not os.path.isfile(solution.source_archive_file_path):
            for project in solution.projects:
                    projects_to_build.append(project)

    # Adding referenced projects too, making sure they are not built twice.

    referenced_projects_to_build = []

    for project in projects_to_build:
        for referenced_project in project.referenced_projects:
            if referenced_project not in referenced_projects_to_build:
                referenced_projects_to_build.append(referenced_project)

    for referenced_project in referenced_projects_to_build:
        if referenced_project not in projects_to_build:
            projects_to_build.append(referenced_project)

    if not projects_to_build:
        output.print_and_log("No projects to build.")
        sys.exit()

    # Mostly for testing purposes.
    random.shuffle(projects_to_build)

    # In real-world scenarios, we need to build the projects repeatedly until all issues are resolved and the code has been committed.
    # Then, we can archive the built binaries and the source code on each platform, effectively marking the projects as "built".

    projects_to_build = dotnet.sort_projects_to_build(projects_to_build)

    output.print_and_log(f"Projects to build:")

    for project in projects_to_build:
        output.print_and_log(project.name, indents=string.leveledIndents[1])

    logging.flush()

    # Incremented at the end of EVERY iteration to avoid restoring the same packages repeatedly.
    # Restoration is automatically executed by SOME of the .NET commands; not all.
    # "build" is almost always the first command we choose, effectively ensuring the first restoration is executed.
    iteration_count = 0

    while True:
        try:
            # From here, some interaction is not logged.

            print(
"""Options:
    1) Build
    2) Update NuGet packages
    3) Rebuild and archive
    4) Exclude a project
    5) Exit""")

            choice = input("Enter your choice: ")

            if choice == "1":
                # Marked as important for attention.
                output.print_and_log_important("Building...")

                for project in projects_to_build:
                    try:
                        output.print_and_log(f"{project.name}:", indents=string.leveledIndents[1])
                        no_restore = iteration_count >= 1
                        output.print_and_log(dotnet.format_result_string_from_messages(project.build(no_restore), indents=string.leveledIndents[2]))

                    except Exception as exception:
                        output.print_and_log_error(f"{exception}", indents=string.leveledIndents[2])

            elif choice == "2":
                output.print_and_log_important("Updating NuGet packages...")

                for project in projects_to_build:
                    try:
                        output.print_and_log(f"{project.name}:", indents=string.leveledIndents[1])
                        output.print_and_log(dotnet.format_result_string_from_messages(project.update_nuget_packages(), indents=string.leveledIndents[2]))

                    except Exception as exception:
                        output.print_and_log_error(f"{exception}", indents=string.leveledIndents[2])

            elif choice == "3":
                output.print_and_log_important("Rebuilding and archiving...")

                archived_solutions = []

                for project in projects_to_build:
                    try:
                        output.print_and_log(f"{project.name}:", indents=string.leveledIndents[1])
                        output.print_and_log(dotnet.format_result_string_from_messages(project.rebuild_and_archive(supported_runtimes, not_archived_directory_names, not_archived_file_names), indents=string.leveledIndents[2]))

                        # When we archive source code, usually, tests have been done and the projects can be built without issues.
                        # So, I wont be implementing one more loop to complicate the interaction.

                        if project.solution not in archived_solutions:
                            output.print_and_log(dotnet.format_result_string_from_messages(project.solution.archive(not_archived_directory_names, not_archived_file_names), indents=string.leveledIndents[2]))
                            archived_solutions.append(project.solution)

                    except Exception as exception:
                        output.print_and_log_error(f"{exception}", indents=string.leveledIndents[2])

            elif choice == "4":
                print("Projects:")

                for index, project in enumerate(projects_to_build):
                    print(f"{string.leveledIndents[1]}{index + 1}) {project.name}")

                try:
                    index = int(input("Enter the index of the project to exclude: ")) - 1

                    if 0 <= index < len(projects_to_build):
                        project = projects_to_build.pop(index)
                        print(f"{project.name} excluded.")

                    else:
                        console.print_warning("Invalid index.") # Not logged.

                except Exception:
                    console.print_warning("Invalid input.")

            elif choice == "5":
                break

        except Exception:
            output.print_and_log_error(traceback.format_exc())

        # Within the loop, at the end of each iteration.
        logging.flush()

        iteration_count += 1

# If we dont specify the exception type, things such as KeyboardInterrupt and SystemExit too may be caught.
except Exception:
    output.print_and_log_error(traceback.format_exc())

finally:
    logging.flush()
    debugging.display_press_enter_key_to_continue_if_not_debugging()
