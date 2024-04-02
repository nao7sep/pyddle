# Created: 2024-03-11
# This script builds and archives all changed projects in the specified repositories directory.

# For logging:
import pyddle_global as global
global.set_main_script_file_path(__file__)

import glob
import os
import pyddle_console as console
import pyddle_debugging as pdebugging
import pyddle_dotnet as dotnet
import pyddle_json_based_kvs as kvs
import pyddle_logging as logging
import pyddle_output as output
import pyddle_string as pstring
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

        if pstring.contains_ignore_case(ignored_directory_names, directory_name):
            if pdebugging.is_debugging():
                output.print_and_log(f"Ignored directory: {directory_name}")

            continue

        solution_file_paths = glob.glob(os.path.join(possible_solution_directory_path, "*.sln"))

        if not solution_file_paths:
            if pdebugging.is_debugging():
                output.print_and_log(f"No solution files found in directory: {directory_name}", colors=console.warning_colors)

            continue

        if len(solution_file_paths) > 1:
            output.print_and_log(f"Multiple solution files found in directory: {directory_name}", colors=console.warning_colors)
            continue

        is_obsolete_solution = pstring.contains_ignore_case(obsolete_solution_names, directory_name)
        solutions.append(dotnet.SolutionInfo(solutions, archives_directory_path, directory_name, possible_solution_directory_path, solution_file_paths[0], is_obsolete_solution))

    if not solutions:
        output.print_and_log(f"No solution directories found.", colors=console.warning_colors)
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
            if pstring.contains_ignore_case(ignored_directory_names, directory_name):
                if pdebugging.is_debugging():
                    output.print_and_log(f"Ignored directory: {solution.name}/{directory_name}")

                continue

            project_file_paths = glob.glob(os.path.join(possible_project_directory_path, "*.csproj"))

            if not project_file_paths:
                if pdebugging.is_debugging():
                    output.print_and_log(f"No project files found in directory: {solution.name}/{directory_name}", colors=console.warning_colors)

                continue

            if len(project_file_paths) > 1:
                output.print_and_log(f"Multiple project files found in directory: {solution.name}/{directory_name}", colors=console.warning_colors)
                continue

            project_directories.append(dotnet.ProjectInfo(solutions, solution, directory_name, possible_project_directory_path, project_file_paths[0]))

        if not project_directories:
            output.print_and_log(f"No project directories found in solution: {solution.name}", colors=console.warning_colors)
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
                output.print_and_log(solution.source_archive_file_path, indents=pstring.leveledIndents[1], colors=console.important_colors)

            for project in sorted(solution.projects, key=lambda x: x.name):
                try:
                    output.print_and_log(f"{project.name} v{project.version_string}", indents=pstring.leveledIndents[1])

                    try:
                        if project.referenced_projects:
                            for referenced_project in sorted(project.referenced_projects, key=lambda x: x.name):
                                output.print_and_log(f"{referenced_project.name} v{referenced_project.version_string}", indents=pstring.leveledIndents[2])

                        else:
                            output.print_and_log(f"No referenced projects found.", indents=pstring.leveledIndents[2])

                        valid_project_count += 1

                    except Exception as exception:
                        # Looks prettier without the project name.
                        output.print_and_log(f"{exception}", indents=pstring.leveledIndents[2], colors=console.error_colors)

                except Exception as exception:
                    output.print_and_log(f"{project.name}: {exception}", indents=pstring.leveledIndents[1], colors=console.error_colors)

        except Exception as exception:
            output.print_and_log(f"{solution.name}: {exception}", colors=console.error_colors)

    if valid_project_count:
        output.print_and_log(f"{valid_project_count} valid projects found.")

    else:
        output.print_and_log("No valid projects found.", colors=console.warning_colors)
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
        output.print_and_log(project.name, indents=pstring.leveledIndents[1])

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
                output.print_and_log("Building...", colors=console.important_colors)

                for project in projects_to_build:
                    try:
                        output.print_and_log(f"{project.name}:", indents=pstring.leveledIndents[1])
                        no_restore = iteration_count >= 1
                        output.print_and_log(dotnet.format_result_string_from_messages(project.build(no_restore), indents=pstring.leveledIndents[2]))

                    except Exception as exception:
                        output.print_and_log(f"{exception}", indents=pstring.leveledIndents[2], colors=console.error_colors)

            elif choice == "2":
                output.print_and_log("Updating NuGet packages...", colors=console.important_colors)

                for project in projects_to_build:
                    try:
                        output.print_and_log(f"{project.name}:", indents=pstring.leveledIndents[1])
                        output.print_and_log(dotnet.format_result_string_from_messages(project.update_nuget_packages(), indents=pstring.leveledIndents[2]))

                    except Exception as exception:
                        output.print_and_log(f"{exception}", indents=pstring.leveledIndents[2], colors=console.error_colors)

            elif choice == "3":
                output.print_and_log("Rebuilding and archiving...", colors=console.important_colors)

                archived_solutions = []

                # BR08 dotnet Commands.json contains (excessively) detailed comments.

                for project in projects_to_build:
                    try:
                        output.print_and_log(f"Cleaning {project.name}:", indents=pstring.leveledIndents[1])
                        output.print_and_log(dotnet.format_result_string_from_messages(project.clean(supported_runtimes, delete_obj_directory=False), indents=pstring.leveledIndents[2]))

                    except Exception as exception:
                        output.print_and_log(f"{exception}", indents=pstring.leveledIndents[2], colors=console.error_colors)

                for project in projects_to_build:
                    try:
                        output.print_and_log(f"Rebuilding and archiving {project.name}:", indents=pstring.leveledIndents[1])
                        output.print_and_log(dotnet.format_result_string_from_messages(project.rebuild_and_archive(supported_runtimes, not_archived_directory_names, not_archived_file_names), indents=pstring.leveledIndents[2]))

                        # When we archive source code, usually, tests have been done and the projects can be built without issues.
                        # So, I wont be implementing one more loop to complicate the interaction.

                        if project.solution not in archived_solutions:
                            output.print_and_log(dotnet.format_result_string_from_messages(project.solution.archive(not_archived_directory_names, not_archived_file_names), indents=pstring.leveledIndents[2]))
                            archived_solutions.append(project.solution)

                    except Exception as exception:
                        output.print_and_log(f"{exception}", indents=pstring.leveledIndents[2], colors=console.error_colors)

            elif choice == "4":
                print("Projects:")

                for index, project in enumerate(projects_to_build):
                    print(f"{pstring.leveledIndents[1]}{index + 1}) {project.name}")

                try:
                    index = int(input("Enter the index of the project to exclude: ")) - 1

                    if 0 <= index < len(projects_to_build):
                        project = projects_to_build.pop(index)
                        print(f"{project.name} excluded.")

                    else:
                        console.print("Invalid index.", colors=console.warning_colors) # Not logged.

                except Exception:
                    console.print("Invalid input.", colors=console.warning_colors)

            elif choice == "5":
                break

        except Exception:
            output.print_and_log(traceback.format_exc(), colors=console.error_colors)

        # Within the loop, at the end of each iteration.
        logging.flush()

        iteration_count += 1

# If we dont specify the exception type, things such as KeyboardInterrupt and SystemExit too may be caught.
except Exception:
    output.print_and_log(traceback.format_exc(), colors=console.error_colors)

finally:
    logging.flush()
    pdebugging.display_press_enter_key_to_continue_if_not_debugging()
