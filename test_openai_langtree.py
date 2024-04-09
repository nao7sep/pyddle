# Created: 2024-04-09
# Tests pyddle_openai_langtree.py.

import json
import threading
import traceback

import pyddle_console as pconsole
import pyddle_debugging as pdebugging
import pyddle_global as pglobal
import pyddle_logging as plogging
import pyddle_openai as popenai
import pyddle_openai_langtree as plangtree
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

SUMMARY_GENERATION_PROMPT = "Please condense the following text into one short paragraph:\n\n{}"
JAPANESE_TRANSLATION_GENERATION_PROMPT = "Please translate the following text into Japanese:\n\n{}"

def generate_summary_attribute_or_japanese_translation(element: plangtree.LangTreeMessage, is_attribute):
    client = popenai.create_openai_client()

    if is_attribute:
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

    else:
        translation = element.generate_translation_with_prompt(
            language=popenai.OpenAiLanguage.JAPANESE,
            prompt=JAPANESE_TRANSLATION_GENERATION_PROMPT.format(element.content),
            client=client)

        plogging.log(f"[Japanese Translation]\n{translation.content}", end="\n\n", flush_=True)

try:
    current_message = None # pylint: disable=invalid-name
    threads = []

    while True:
        command = pconsole.input_command("Command: ")

        if not command:
            pconsole.print("Invalid command.", colors=pconsole.ERROR_COLORS)

        else:
            if (pstring.equals_ignore_case(command.command, "system") or
                pstring.equals_ignore_case(command.command, "user")):

                user_role = popenai.OpenAiRole.SYSTEM if len(command.command) == 6 else popenai.OpenAiRole.USER
                content = command.get_remaining_args_as_str(0) # pylint: disable=invalid-name

                if current_message is None:
                    current_message = plangtree.LangTreeMessage(user_role=user_role, content=content)

                else:
                    current_message = current_message.create_child_message(user_role=user_role, content=content)

                thread1 = threading.Thread(target=generate_summary_attribute_or_japanese_translation, args=(current_message, True))
                threads.append(thread1)
                thread1.start()

                thread2 = threading.Thread(target=generate_summary_attribute_or_japanese_translation, args=(current_message, False))
                threads.append(thread2)
                thread2.start()

                if len(command.command) == 4:
                    context_builder = plangtree.get_langtree_default_context_builder()
                    messages = context_builder.build_messages(current_message)

                    messages_json_str = json.dumps(messages, ensure_ascii=False, indent=4)
                    plogging.log(f"[Messages]\n{messages_json_str}", end="\n\n", flush_=True)

                    current_message = current_message.generate_child_message_with_messages(messages)

                    pconsole.print("Response:")
                    pconsole.print_lines(pstring.splitlines(current_message.content), indents=pstring.LEVELED_INDENTS[1])

                    thread3 = threading.Thread(target=generate_summary_attribute_or_japanese_translation, args=(current_message, True))
                    threads.append(thread3)
                    thread3.start()

                    thread4 = threading.Thread(target=generate_summary_attribute_or_japanese_translation, args=(current_message, False))
                    threads.append(thread4)
                    thread4.start()

            elif pstring.equals_ignore_case(command.command, "exit"):
                break

            else:
                pconsole.print("Invalid command.", colors=pconsole.ERROR_COLORS)

    for thread in threads:
        thread.join()

    if current_message is not None:
        root_message = current_message.get_root_element()
        json_str = json.dumps(root_message.serialize_to_dict(), ensure_ascii=False, indent=4)

        pconsole.print("Serialized root message:")
        pconsole.print_lines(pstring.splitlines(json_str), indents=pstring.LEVELED_INDENTS[1])

        new_root_message = plangtree.LangTreeMessage.deserialize_from_dict(json.loads(json_str))
        new_json_str = json.dumps(new_root_message.serialize_to_dict(), ensure_ascii=False, indent=4)

        pconsole.print(f"new_json_str == json_str: {new_json_str == json_str}")

except Exception: # pylint: disable=broad-except
    pconsole.print(traceback.format_exc(), colors=pconsole.ERROR_COLORS)

finally:
    pdebugging.display_press_enter_key_to_continue_if_not_debugging()
