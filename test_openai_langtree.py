﻿# Created: 2024-04-10
# Tests pyddle_openai_langtree.py.

import json
import os
import sys
import threading
import traceback

import pyddle_console as pconsole
import pyddle_debugging as pdebugging
import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_logging as plogging
import pyddle_openai as popenai
import pyddle_openai_langtree as plangtree
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

# Generated by GitHub Copilot:
JAPANESE_TRANSLATION_PROMPT = "Translate the following text into Japanese:"
RUSSIAN_TRANSLATION_PROMPT = "Translate the following text into Russian:"

def translate(element: plangtree.LangTreeMessage, language: popenai.OpenAiLanguage):
    client = popenai.create_openai_client()

    if language == popenai.OpenAiLanguage.JAPANESE:
        prompt = JAPANESE_TRANSLATION_PROMPT

    elif language == popenai.OpenAiLanguage.RUSSIAN:
        prompt = RUSSIAN_TRANSLATION_PROMPT

    else:
        raise RuntimeError(f"Invalid language: {language}")

    element.generate_translation_with_prompt(
        language = language,
        prompt = f"{prompt}\n\n{element.content}",
        client = client)

def create_sibling_message(element: plangtree.LangTreeMessage, user_role: popenai.OpenAiRole, content: str):
    if element is None:
        new_current_message = plangtree.LangTreeMessage(user_role = user_role, content = content)

    else:
        new_current_message = element.create_sibling_message(user_role = user_role, content = content)

    # System messages arent translated.

    if user_role == popenai.OpenAiRole.USER:
        # Comments: SH77 langtree-related Comments.json

        threads.append(threading.Thread(target = translate, args = (new_current_message, popenai.OpenAiLanguage.JAPANESE)))
        threads[-1].start()

        threads.append(threading.Thread(target = translate, args = (new_current_message, popenai.OpenAiLanguage.RUSSIAN)))
        threads[-1].start()

        context_builder = plangtree.get_langtree_default_context_builder()
        context = context_builder.build(new_current_message)

        statistics_lines = plangtree.LangTreeContext.statistics_to_lines(context.get_statistics(), all_tokens = True)

        plogging.log("[Statistics]") # [Content Statistics] sounds a little redundant.
        plogging.log_lines(statistics_lines, indents = pstring.LEVELED_INDENTS[1])
        plogging.log("", flush_ = True)

        messages_json_str = json.dumps(context.messages, ensure_ascii = False, indent = 4)
        plogging.log(f"[Context]\n{messages_json_str}", end = "\n\n", flush_ = True)

        response = new_current_message.start_generating_message_with_messages(context.messages)

        # Collecting what the AI has returned, excluding falsy values.
        # As of 2024-04-12, at least one time, None is returned.
        chunk_deltas = []

        chunk_str_reader = pstring.ChunkStrReader(indents = pstring.LEVELED_INDENTS[1])

        pconsole.print("Response:")

        for chunk in response:
            chunk_delta = popenai.openai_extract_first_delta(chunk)

            if chunk_delta:
                chunk_deltas.append(chunk_delta)
                chunk_str_reader.add_chunk(chunk_delta)

                chunk_str = chunk_str_reader.read_str()
                pconsole.print(chunk_str, end = "")
                sys.stdout.flush() # Without this, output may come out line by line.

        # ChunkStrReader doesnt return the remaining chunk if it ends with a line break and waits for the next one to determine whether indents must be added or not.
        # When the interaction has ended, we need to receive the last chunk (if any) and print it as-is because it may contain a visible character right before the line break.
        chunk_str = chunk_str_reader.read_str(force = True)
        end_ = "" if chunk_str.endswith("\n") else "\n" # If we want to do this precisely, we'd need to analyze the last part of "content".
        pconsole.print(chunk_str, end = end_)

        content = "".join(chunk_deltas)

        plogging.log(f"[Response]\n{content}", end = "\n\n", flush_ = True)

        new_current_message = new_current_message.create_sibling_message(
            user_role = popenai.OpenAiRole.ASSISTANT,
            content = content)

        threads.append(threading.Thread(target = translate, args = (new_current_message, popenai.OpenAiLanguage.JAPANESE)))
        threads[-1].start()

        threads.append(threading.Thread(target = translate, args = (new_current_message, popenai.OpenAiLanguage.RUSSIAN)))
        threads[-1].start()

    return new_current_message

try:
    pfs.make_and_move_to_output_subdirectory()

    JSON_FILE_PATH = "test_openai_langtree.json"

    current_message: plangtree.LangTreeMessage | None = None # pylint: disable = invalid-name

    if os.path.isfile(JSON_FILE_PATH):
        json_file_contents = pfs.read_all_text_from_file(JSON_FILE_PATH)
        json_dictionary = json.loads(json_file_contents)
        current_message = plangtree.LangTreeMessage.deserialize_from_dict(json_dictionary)

        while True:
            if current_message.child_messages:
                current_message = current_message.child_messages[-1]

            else:
                break

    threads: list[threading.Thread] = []

    def _save():
        root_message = current_message.get_root_element()
        json_str_ = json.dumps(root_message.serialize_to_dict(), ensure_ascii = False, indent = 4)
        pfs.write_all_text_to_file(JSON_FILE_PATH, json_str_)
        return json_str_

    while True:
        command_str = input("Command: ") # We'll need the entire command string.
        command = pconsole.parse_command_str(command_str)

        if not command:
            pconsole.print("Invalid command.", indents = pstring.LEVELED_INDENTS[1], colors = pconsole.ERROR_COLORS)

        else:
            if pstring.equals_ignore_case(command.command, "system"):
                current_message = create_sibling_message(current_message, popenai.OpenAiRole.SYSTEM, command.get_remaining_args_as_str(0))
                _save()

            elif pstring.equals_ignore_case(command.command, "delete") and len(command.args) == 0:
                if current_message:
                    previous_message = current_message.get_previous_message()

                    # Explicit implementation.
                    # If there's an element to move back to, the current one is removed from the list.
                    # If not, it automatically means it's the root element, so we set it to None.

                    if previous_message:
                        current_message.parent_element.child_messages.remove(current_message)
                        current_message = previous_message
                        _save() # Only when the JSON file has been affected.

                    else:
                        current_message = None # pylint: disable = invalid-name

                    pconsole.print("Deleted message.", indents = pstring.LEVELED_INDENTS[1], colors = pconsole.IMPORTANT_COLORS)

                    if current_message:
                        pconsole.print(f"Current message: {pstring.extract_first_part(current_message.content)}", indents = pstring.LEVELED_INDENTS[1])

                    else:
                        pconsole.print("No current message.", indents = pstring.LEVELED_INDENTS[1], colors = pconsole.IMPORTANT_COLORS)

                else:
                    pconsole.print("No messages to delete.", indents = pstring.LEVELED_INDENTS[1], colors = pconsole.ERROR_COLORS)

            elif pstring.equals_ignore_case(command.command, "exit") and len(command.args) == 0:
                break

            else:
                current_message = create_sibling_message(current_message, popenai.OpenAiRole.USER, command_str)
                _save()

    # If at least one thread has become a zombie, this operation might not end.
    # In production code, we should set a timeout and (passively) notify the caller that the attribute/translation hasnt been generated.

    for thread in threads:
        thread.join()

    if current_message is not None:
        json_str = _save() # Saving the translations.

        new_root_message = plangtree.LangTreeMessage.deserialize_from_dict(json.loads(json_str))
        new_json_str = json.dumps(new_root_message.serialize_to_dict(), ensure_ascii = False, indent = 4)

        colors = pconsole.IMPORTANT_COLORS if new_json_str == json_str else pconsole.ERROR_COLORS
        pconsole.print(f"new_json_str == json_str: {new_json_str == json_str}", colors = colors)

except Exception: # pylint: disable = broad-except
    pconsole.print(traceback.format_exc(), colors = pconsole.ERROR_COLORS)

finally:
    pdebugging.display_press_enter_key_to_continue_if_not_debugging()
