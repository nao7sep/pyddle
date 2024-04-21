# Created: 2024-04-20
# An experimental script to check code using OpenAI's GPT-4 model.

import os
import sys
import traceback

import pyddle_console as pconsole
import pyddle_datetime as pdatetime
import pyddle_debugging as pdebugging
import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_kvs as pkvs
import pyddle_openai as popenai
import pyddle_path as ppath
import pyddle_prompts as pprompts
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

try:
    KVS_KEY_PREFIX = "code_checker/"

    pyddle_directory_path = pkvs.read_from_merged_data(f"{KVS_KEY_PREFIX}pyddle_directory_path")
    pconsole.print(f"pyddle_directory_path: {pyddle_directory_path}")

    project_directory_paths_str = pkvs.read_from_merged_data(f"{KVS_KEY_PREFIX}project_directory_paths") or ""
    project_directory_paths = sorted([path_ for path_ in (path.strip() for path in project_directory_paths_str.split("|")) if path_])
    pconsole.print(f"project_directory_paths: {project_directory_paths}")

    def check_code(project_directory_path_, file_name_, prompt):
        file_path = os.path.join(project_directory_path_, file_name_)
        code = pfs.read_all_text_from_file(file_path)

        messages: list[dict[str, str]] = []
        popenai.add_system_message(messages, pprompts.SYSTEM_MESSAGE_FOR_TEXT_AND_MULTI_SENTENCE_PROMPT_MESSAGES)
        popenai.add_user_message(messages, pprompts.get_text_message(code))
        popenai.add_user_message(messages, pprompts.get_multi_sentence_prompt_message(prompt))

        response = popenai.create_chat_completions(
            model = popenai.Model.GPT_4_TURBO,
            messages = messages,
            stream = True)

        chunk_deltas: list[str] = []
        reader = pstring.ChunkStrReader(indents = pstring.LEVELED_INDENTS[1])

        pconsole.print(f"Response for {file_name_}:")

        for chunk in response:
            chunk_delta = popenai.extract_first_delta(chunk)

            if chunk_delta:
                chunk_deltas.append(chunk_delta)
                reader.add_chunk(chunk_delta)

                chunk_str = reader.read_str()
                pconsole.print(chunk_str, end = "")
                sys.stdout.flush()

        chunk_str = reader.read_str(force = True)
        end = "" if chunk_str.endswith("\n") else "\n"
        pconsole.print(chunk_str, end = end)

        response_str = "".join(chunk_deltas).rstrip()

        utc_now = pdatetime.get_utc_now()
        date_string = utc_now.strftime("%Y%m%dT%H%M%SZ")
        file_name_without_extension, _ = os.path.splitext(file_name_)
        log_file_name = f"{date_string}-{file_name_without_extension}.log"
        project_name = ppath.basename(project_directory_path_)
        log_file_path = os.path.join(pyddle_directory_path, "code_checks", project_name, log_file_name)

        file_contents: list[str] = []
        file_contents.append(f"UTC: {utc_now.isoformat()}\n")
        file_contents.append(f"File: {project_name}/{file_name_}\n")
        file_contents.append(f"Prompt: {prompt}\n")
        file_contents.append(f"Code Tokens: {popenai.get_gpt_4_turbo_token_counter().count(code)}\n")
        file_contents.append(f"Response Tokens: {popenai.get_gpt_4_turbo_token_counter().count(response_str)}\n\n")
        file_contents.append(response_str)
        file_contents.append("\n")
        file_content_str = "".join(file_contents)

        pfs.create_parent_directory(log_file_path)
        pfs.write_all_text_to_file(log_file_path, file_content_str)
        pconsole.print(f"Log file created: {log_file_path}")

    def get_ignored_file_names(project_directory_path_):
        project_name = ppath.basename(project_directory_path_)
        ignored_file_path = os.path.join(pyddle_directory_path, "code_checks", project_name, "ignored.txt")

        if os.path.isfile(ignored_file_path):
            file_content_lines = pstring.splitlines(pfs.read_all_text_from_file(ignored_file_path))
            return [path for path in file_content_lines if path and not path.startswith("#")]

        return []

    CHECK_PROMPT = "Potential issues and improvements, as many and detailed as possible, please."

    if not pyddle_directory_path:
        pconsole.print("pyddle_directory_path not set.", colors = pconsole.ERROR_COLORS)
        sys.exit()

    if not project_directory_paths:
        pconsole.print("project_directory_paths not set.", colors = pconsole.ERROR_COLORS)
        sys.exit()

    pconsole.print("Projects:")
    project_names = [ppath.basename(path) for path in project_directory_paths]
    pconsole.print_numbered_options(project_names, indents = pstring.LEVELED_INDENTS[1])
    project_index = pconsole.input_number("Select project or else to close: ") - 1

    if project_index < 0 or project_index >= len(project_directory_paths):
        sys.exit()

    project_directory_path = project_directory_paths[project_index]
    ignored_file_names = get_ignored_file_names(project_directory_path)
    file_paths: list[str] = []

    ignored_file_count = 0 # pylint: disable = invalid-name

    for file_name in os.listdir(project_directory_path):
        if pstring.endswith_ignore_case(file_name, ".py"):
            if not pstring.contains_ignore_case(ignored_file_names, file_name):
                file_paths.append(os.path.join(project_directory_path, file_name))

            else:
                ignored_file_count += 1

    file_paths.sort()

    pconsole.print(f"{len(file_paths) + ignored_file_count} Python files found.")
    pconsole.print(f"{ignored_file_count} files ignored.")

    if not file_paths:
        sys.exit()

    while True:
        pconsole.print("Files:")
        file_names = [ppath.basename(path) for path in file_paths]
        pconsole.print_numbered_options(file_names, indents = pstring.LEVELED_INDENTS[1])
        file_index_str = input("Select file or \"all\" or else to close: ")

        try:
            file_index = int(file_index_str)

            if file_index < 0 or file_index >= len(file_paths):
                break

            check_code(project_directory_path, file_names[file_index], CHECK_PROMPT)

            continue

        except Exception: # pylint: disable = broad-except
            pass

        if pstring.equals_ignore_case(file_index_str, "all"):
            for file_name in file_names:
                check_code(project_directory_path, file_name, CHECK_PROMPT)

            continue

        break

except Exception: # pylint: disable = broad-except
    pconsole.print(traceback.format_exc(), colors = pconsole.ERROR_COLORS)

finally:
    pdebugging.display_press_enter_key_to_continue_if_not_debugging()
