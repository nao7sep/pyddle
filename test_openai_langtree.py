﻿# Created: 2024-04-09
# Tests pyddle_openai_langtree.py.

import enum
import json
import os
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

TITLE_GENERATION_PROMPT = "Please generate a title for the following text:\n\n{}"
SUMMARY_GENERATION_PROMPT = "Please generate a summary for the following text:\n\n{}"
JAPANESE_TRANSLATION_GENERATION_PROMPT = "Please generate a Japanese translation for the following text:\n\n{}"

class GenerationMode(enum.Enum):
    TITLE = 1
    SUMMARY = 2
    JAPANESE_TRANSLATION = 3

def generate_stuff(element: plangtree.LangTreeMessage, mode: GenerationMode):
    client = popenai.create_openai_client()

    if mode == GenerationMode.TITLE:
        attribute = element.generate_attribute_with_prompt(
            name="title",
            prompt=TITLE_GENERATION_PROMPT.format(element.content),
            client=client)

        plogging.log(f"[Title]\n{attribute.value}", end="\n\n", flush_=True)

        translation = attribute.generate_translation_with_prompt(
            language=popenai.OpenAiLanguage.JAPANESE,
            prompt=JAPANESE_TRANSLATION_GENERATION_PROMPT.format(attribute.value),
            client=client)

        plogging.log(f"[Japanese Translation of Title]\n{translation.content}", end="\n\n", flush_=True)

    elif mode == GenerationMode.SUMMARY:
        attribute = element.generate_attribute_with_prompt(
            name="summary",
            prompt=SUMMARY_GENERATION_PROMPT.format(element.content),
            client=client)

        plogging.log(f"[Summary]\n{attribute.value}", end="\n\n", flush_=True)

        translation = attribute.generate_translation_with_prompt(
            language=popenai.OpenAiLanguage.JAPANESE,
            prompt=JAPANESE_TRANSLATION_GENERATION_PROMPT.format(attribute.value),
            client=client)

        plogging.log(f"[Japanese Translation of Summary]\n{translation.content}", end="\n\n", flush_=True)

    elif mode == GenerationMode.JAPANESE_TRANSLATION:
        translation = element.generate_translation_with_prompt(
            language=popenai.OpenAiLanguage.JAPANESE,
            prompt=JAPANESE_TRANSLATION_GENERATION_PROMPT.format(element.content),
            client=client)

        plogging.log(f"[Japanese Translation]\n{translation.content}", end="\n\n", flush_=True)

    else:
        raise RuntimeError(f"Invalid mode: {mode}")

def create_child_message(current_message_, user_role: popenai.OpenAiRole, content: str):
    if current_message_ is None:
        new_current_message = plangtree.LangTreeMessage(user_role=user_role, content=content)

    else:
        new_current_message = current_message_.create_child_message(user_role=user_role, content=content)

    thread1 = threading.Thread(target=generate_stuff, args=(new_current_message, GenerationMode.TITLE))
    threads.append(thread1)
    thread1.start()

    thread2 = threading.Thread(target=generate_stuff, args=(new_current_message, GenerationMode.SUMMARY))
    threads.append(thread2)
    thread2.start()

    thread3 = threading.Thread(target=generate_stuff, args=(new_current_message, GenerationMode.JAPANESE_TRANSLATION))
    threads.append(thread3)
    thread3.start()

    if user_role == popenai.OpenAiRole.USER:
        context_builder = plangtree.get_langtree_default_context_builder()
        messages = context_builder.build_messages(new_current_message)

        messages_json_str = json.dumps(messages, ensure_ascii=False, indent=4)
        plogging.log(f"[Context]\n{messages_json_str}", end="\n\n", flush_=True)

        new_current_message = new_current_message.generate_child_message_with_messages(messages)
        plogging.log(f"[Response]\n{new_current_message.content}", end="\n\n", flush_=True)

        pconsole.print("Response:")
        pconsole.print_lines(pstring.splitlines(new_current_message.content), indents=pstring.LEVELED_INDENTS[1])

        thread4 = threading.Thread(target=generate_stuff, args=(new_current_message, GenerationMode.TITLE))
        threads.append(thread4)
        thread4.start()

        thread5 = threading.Thread(target=generate_stuff, args=(new_current_message, GenerationMode.SUMMARY))
        threads.append(thread5)
        thread5.start()

        thread6 = threading.Thread(target=generate_stuff, args=(new_current_message, GenerationMode.JAPANESE_TRANSLATION))
        threads.append(thread6)
        thread6.start()

    return new_current_message

try:
    pfs.make_and_move_to_output_subdirectory()

    JSON_FILE_PATH = "test_openai_langtree.json"

    current_message = None # pylint: disable=invalid-name

    if os.path.isfile(JSON_FILE_PATH):
        json_file_contents = pfs.read_all_text_from_file(JSON_FILE_PATH)
        json_dictionary = json.loads(json_file_contents)
        current_message = plangtree.LangTreeMessage.deserialize_from_dict(json_dictionary)

        while True:
            if current_message.child_messages:
                current_message = current_message.child_messages[-1]

            else:
                break

    threads = []

    while True:
        command_str = input("Command: ")
        command = pconsole.parse_command_str(command_str)

        if not command:
            pconsole.print("Invalid command.", colors=pconsole.ERROR_COLORS)

        else:
            if pstring.equals_ignore_case(command.command, "system"):
                current_message = create_child_message(current_message, popenai.OpenAiRole.SYSTEM, command.get_remaining_args_as_str(0))

            elif pstring.equals_ignore_case(command.command, "exit"):
                break

            else:
                current_message = create_child_message(current_message, popenai.OpenAiRole.USER, command_str)

    for thread in threads:
        thread.join()

    if current_message is not None:
        root_message = current_message.get_root_element()
        json_str = json.dumps(root_message.serialize_to_dict(), ensure_ascii=False, indent=4)
        pfs.write_all_text_to_file(JSON_FILE_PATH, json_str)

        new_root_message = plangtree.LangTreeMessage.deserialize_from_dict(json.loads(json_str))
        new_json_str = json.dumps(new_root_message.serialize_to_dict(), ensure_ascii=False, indent=4)

        colors = pconsole.IMPORTANT_COLORS if new_json_str == json_str else pconsole.ERROR_COLORS
        pconsole.print(f"new_json_str == json_str: {new_json_str == json_str}", colors=colors)

except Exception: # pylint: disable=broad-except
    pconsole.print(traceback.format_exc(), colors=pconsole.ERROR_COLORS)

finally:
    pdebugging.display_press_enter_key_to_continue_if_not_debugging()
