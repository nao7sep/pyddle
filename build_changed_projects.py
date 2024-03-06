import pyddle_debugging as debugging
import pyddle_dotnet as dotnet
import pyddle_json_based_kvs as kvs
import pyddle_string as string
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

    # A neutral character that is rarely used in project names.
    value_separator = "|"

    ignored_directory_names = []
    ignored_directory_names_string = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}ignored_directory_names")

    if ignored_directory_names_string:
        ignored_directory_names = [value.strip() for value in ignored_directory_names_string.split(value_separator) if value.strip()]

        if ignored_directory_names:
            print(f"ignored_directory_names: {ignored_directory_names}")

    obsolete_project_names = []
    obsolete_project_names_string = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}obsolete_project_names")

    if obsolete_project_names_string:
        obsolete_project_names = [value.strip() for value in obsolete_project_names_string.split(value_separator) if value.strip()]

        if obsolete_project_names:
            print(f"obsolete_project_names: {obsolete_project_names}")

# If we dont specify the exception type, things such as KeyboardInterrupt and SystemExit too may be caught.
except Exception:
    traceback.print_exc()

debugging.display_press_enter_key_to_continue_if_not_debugging()
