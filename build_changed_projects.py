# Created: 2024-03-11
# This script builds and archives all changed projects in the specified repositories directory.

import glob
import os
import random
import sys
import traceback

import pyddle_console as pconsole
import pyddle_debugging as pdebugging
import pyddle_dotnet as pdotnet
import pyddle_global as pglobal
import pyddle_json_based_kvs as pkvs
import pyddle_logging as plogging
import pyddle_output as poutput
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

try:
    # ------------------------------------------------------------------------------
    #     Load settings
    # ------------------------------------------------------------------------------

    KVS_KEY_PREFIX = "build_changed_projects/"

    repositories_directory_path = pkvs.read_from_merged_kvs_data(f"{KVS_KEY_PREFIX}repositories_directory_path")
    poutput.print_and_log(f"repositories_directory_path: {repositories_directory_path}")

    archives_directory_path = pkvs.read_from_merged_kvs_data(f"{KVS_KEY_PREFIX}archives_directory_path")
    poutput.print_and_log(f"archives_directory_path: {archives_directory_path}")

    # A neutral character that is rarely used in solution/project names.
    VALUE_SEPARATOR = "|"

    ignored_directory_names = []
    ignored_directory_names_string = pkvs.read_from_merged_kvs_data(f"{KVS_KEY_PREFIX}ignored_directory_names")

    if ignored_directory_names_string:
        ignored_directory_names = [value.strip() for value in ignored_directory_names_string.split(VALUE_SEPARATOR) if value.strip()]

        if ignored_directory_names:
            poutput.print_and_log(f"ignored_directory_names: {ignored_directory_names}")

    obsolete_solution_names = []
    obsolete_solution_names_string = pkvs.read_from_merged_kvs_data(f"{KVS_KEY_PREFIX}obsolete_solution_names")

    if obsolete_solution_names_string:
        obsolete_solution_names = [value.strip() for value in obsolete_solution_names_string.split(VALUE_SEPARATOR) if value.strip()]

        if obsolete_solution_names:
            poutput.print_and_log(f"obsolete_solution_names: {obsolete_solution_names}")

    supported_runtimes = []
    supported_runtimes_string = pkvs.read_from_merged_kvs_data(f"{KVS_KEY_PREFIX}supported_runtimes")

    if supported_runtimes_string:
        supported_runtimes = [value.strip() for value in supported_runtimes_string.split(VALUE_SEPARATOR) if value.strip()]

        if supported_runtimes:
            poutput.print_and_log(f"supported_runtimes: {supported_runtimes}")

    not_archived_directory_names = []
    not_archived_directory_names_string = pkvs.read_from_merged_kvs_data(f"{KVS_KEY_PREFIX}not_archived_directory_names")

    if not_archived_directory_names_string:
        not_archived_directory_names = [value.strip() for value in not_archived_directory_names_string.split(VALUE_SEPARATOR) if value.strip()]

        if not_archived_directory_names:
            poutput.print_and_log(f"not_archived_directory_names: {not_archived_directory_names}")

    not_archived_file_names = []
    not_archived_file_names_string = pkvs.read_from_merged_kvs_data(f"{KVS_KEY_PREFIX}not_archived_file_names")

    if not_archived_file_names_string:
        not_archived_file_names = [value.strip() for value in not_archived_file_names_string.split(VALUE_SEPARATOR) if value.strip()]

        if not_archived_file_names:
            poutput.print_and_log(f"not_archived_file_names: {not_archived_file_names}")

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
                poutput.print_and_log(f"Ignored directory: {directory_name}")

            continue

        solution_file_paths = glob.glob(os.path.join(possible_solution_directory_path, "*.sln"))

        if not solution_file_paths:
            if pdebugging.is_debugging():
                poutput.print_and_log(f"No solution files found in directory: {directory_name}", colors = pconsole.WARNING_COLORS)

            continue

        if len(solution_file_paths) > 1:
            poutput.print_and_log(f"Multiple solution files found in directory: {directory_name}", colors = pconsole.WARNING_COLORS)
            continue

        is_obsolete_solution = pstring.contains_ignore_case(obsolete_solution_names, directory_name) # pylint: disable=invalid-name
        solutions.append(pdotnet.SolutionInfo(solutions, archives_directory_path, directory_name, possible_solution_directory_path, solution_file_paths[0], is_obsolete_solution))

    if not solutions:
        poutput.print_and_log("No solution directories found.", colors = pconsole.WARNING_COLORS)
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
                    poutput.print_and_log(f"Ignored directory: {solution.name}/{directory_name}")

                continue

            project_file_paths = glob.glob(os.path.join(possible_project_directory_path, "*.csproj"))

            if not project_file_paths:
                if pdebugging.is_debugging():
                    poutput.print_and_log(f"No project files found in directory: {solution.name}/{directory_name}", colors = pconsole.WARNING_COLORS)

                continue

            if len(project_file_paths) > 1:
                poutput.print_and_log(f"Multiple project files found in directory: {solution.name}/{directory_name}", colors = pconsole.WARNING_COLORS)
                continue

            project_directories.append(pdotnet.ProjectInfo(solutions, solution, directory_name, possible_project_directory_path, project_file_paths[0]))

        if not project_directories:
            poutput.print_and_log(f"No project directories found in solution: {solution.name}", colors = pconsole.WARNING_COLORS)
            continue

        solution.projects = project_directories

    # ------------------------------------------------------------------------------
    #     Read version strings, references, etc
    # ------------------------------------------------------------------------------

    valid_project_count = 0 # pylint: disable=invalid-name

    for solution in sorted(solutions, key=lambda x: x.name):
        try:
            poutput.print_and_log(f"{solution.name} v{solution.common_version_string}")

            if not os.path.isfile(solution.source_archive_file_path):
                poutput.print_and_log(solution.source_archive_file_path, indents=pstring.LEVELED_INDENTS[1], colors = pconsole.IMPORTANT_COLORS)

            for project in sorted(solution.projects, key=lambda x: x.name):
                try:
                    poutput.print_and_log(f"{project.name} v{project.version_string}", indents=pstring.LEVELED_INDENTS[1])

                    try:
                        if project.referenced_projects:
                            for referenced_project in sorted(project.referenced_projects, key=lambda x: x.name):
                                poutput.print_and_log(f"{referenced_project.name} v{referenced_project.version_string}", indents=pstring.LEVELED_INDENTS[2])

                        else:
                            poutput.print_and_log("No referenced projects found.", indents=pstring.LEVELED_INDENTS[2])

                        valid_project_count += 1

                    except Exception as exception: # pylint: disable=broad-except
                        # Looks prettier without the project name.
                        poutput.print_and_log(f"{exception}", indents=pstring.LEVELED_INDENTS[2], colors = pconsole.ERROR_COLORS)

                except Exception as exception: # pylint: disable=broad-except
                    poutput.print_and_log(f"{project.name}: {exception}", indents=pstring.LEVELED_INDENTS[1], colors = pconsole.ERROR_COLORS)

        except Exception as exception: # pylint: disable=broad-except
            poutput.print_and_log(f"{solution.name}: {exception}", colors = pconsole.ERROR_COLORS)

    if valid_project_count:
        poutput.print_and_log(f"{valid_project_count} valid projects found.")

    else:
        poutput.print_and_log("No valid projects found.", colors = pconsole.WARNING_COLORS)
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
        poutput.print_and_log("No projects to build.")
        sys.exit()

    # Mostly for testing purposes.
    random.shuffle(projects_to_build)

    # In real-world scenarios, we need to build the projects repeatedly until all issues are resolved and the code has been committed.
    # Then, we can archive the built binaries and the source code on each platform, effectively marking the projects as "built".

    projects_to_build = pdotnet.sort_projects_to_build(projects_to_build)

    poutput.print_and_log("Projects to build:")

    for project in projects_to_build:
        poutput.print_and_log(project.name, indents=pstring.LEVELED_INDENTS[1])

    plogging.flush()

    # Incremented at the end of EVERY iteration to avoid restoring the same packages repeatedly.
    # Restoration is automatically executed by SOME of the .NET commands; not all.
    # "build" is almost always the first command we choose, effectively ensuring the first restoration is executed.
    iteration_count = 0 # pylint: disable=invalid-name

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
                poutput.print_and_log("Building...", colors = pconsole.IMPORTANT_COLORS)

                for project in projects_to_build:
                    try:
                        poutput.print_and_log(f"{project.name}:", indents=pstring.LEVELED_INDENTS[1])
                        no_restore = iteration_count >= 1 # pylint: disable=invalid-name
                        poutput.print_and_log(pdotnet.format_result_string_from_messages(project.build(no_restore), indents=pstring.LEVELED_INDENTS[2]))

                    except Exception as exception: # pylint: disable=broad-except
                        poutput.print_and_log(f"{exception}", indents=pstring.LEVELED_INDENTS[2], colors = pconsole.ERROR_COLORS)

            elif choice == "2":
                poutput.print_and_log("Updating NuGet packages...", colors = pconsole.IMPORTANT_COLORS)

                for project in projects_to_build:
                    try:
                        poutput.print_and_log(f"{project.name}:", indents=pstring.LEVELED_INDENTS[1])
                        poutput.print_and_log(pdotnet.format_result_string_from_messages(project.update_nuget_packages(), indents=pstring.LEVELED_INDENTS[2]))

                    except Exception as exception: # pylint: disable=broad-except
                        poutput.print_and_log(f"{exception}", indents=pstring.LEVELED_INDENTS[2], colors = pconsole.ERROR_COLORS)

            elif choice == "3":
                poutput.print_and_log("Rebuilding and archiving...", colors = pconsole.IMPORTANT_COLORS)

                archived_solutions = []

                # BR08 dotnet Commands.json contains (excessively) detailed comments.

                for project in projects_to_build:
                    try:
                        poutput.print_and_log(f"Cleaning {project.name}:", indents=pstring.LEVELED_INDENTS[1])
                        poutput.print_and_log(pdotnet.format_result_string_from_messages(project.clean(supported_runtimes, delete_obj_directory=False), indents=pstring.LEVELED_INDENTS[2]))

                    except Exception as exception: # pylint: disable=broad-except
                        poutput.print_and_log(f"{exception}", indents=pstring.LEVELED_INDENTS[2], colors = pconsole.ERROR_COLORS)

                for project in projects_to_build:
                    try:
                        poutput.print_and_log(f"Rebuilding and archiving {project.name}:", indents=pstring.LEVELED_INDENTS[1])
                        poutput.print_and_log(pdotnet.format_result_string_from_messages(project.rebuild_and_archive(supported_runtimes, not_archived_directory_names, not_archived_file_names), indents=pstring.LEVELED_INDENTS[2]))

                        # When we archive source code, usually, tests have been done and the projects can be built without issues.
                        # So, I wont be implementing one more loop to complicate the interaction.

                        if project.solution not in archived_solutions:
                            poutput.print_and_log(pdotnet.format_result_string_from_messages(project.solution.archive(not_archived_directory_names, not_archived_file_names), indents=pstring.LEVELED_INDENTS[2]))
                            archived_solutions.append(project.solution)

                    except Exception as exception: # pylint: disable=broad-except
                        poutput.print_and_log(f"{exception}", indents=pstring.LEVELED_INDENTS[2], colors = pconsole.ERROR_COLORS)

            elif choice == "4":
                print("Projects:")

                for index, project in enumerate(projects_to_build):
                    print(f"{pstring.LEVELED_INDENTS[1]}{index + 1}) {project.name}")

                try:
                    index = int(input("Enter the index of the project to exclude: ")) - 1

                    if 0 <= index < len(projects_to_build):
                        project = projects_to_build.pop(index)
                        print(f"{project.name} excluded.")

                    else:
                        pconsole.print("Invalid index.", colors = pconsole.WARNING_COLORS) # Not logged.

                except Exception: # pylint: disable=broad-except
                    pconsole.print("Invalid input.", colors = pconsole.WARNING_COLORS)

            elif choice == "5":
                break

        except Exception: # pylint: disable=broad-except
            poutput.print_and_log(traceback.format_exc(), colors = pconsole.ERROR_COLORS)

        # Within the loop, at the end of each iteration.
        plogging.flush()

        iteration_count += 1

# If we dont specify the exception type, things such as KeyboardInterrupt and SystemExit too may be caught.
except Exception: # pylint: disable=broad-except
    poutput.print_and_log(traceback.format_exc(), colors = pconsole.ERROR_COLORS)

finally:
    plogging.flush()
    pdebugging.display_press_enter_key_to_continue_if_not_debugging()
