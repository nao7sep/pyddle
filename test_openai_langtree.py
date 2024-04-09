# Created: 2024-04-09
# Tests pyddle_openai_langtree.py.

import json
import threading
import traceback

import pyddle_console as pconsole
import pyddle_debugging as pdebugging
import pyddle_global as pglobal
import pyddle_openai as popenai
import pyddle_openai_langtree as plangtree
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

def generate_summary_attribute_or_japanese_translation(element: plangtree.LangTreeMessage, is_attribute):
    client = popenai.create_openai_client()

    if is_attribute:
        element.generate_attribute_with_prompt(
            name="summary",
            prompt=f"Please summarize the following text:\n\n{element.content}",
            client=client)

    else:
        element.generate_translation_with_prompt(
            language=popenai.OpenAiLanguage.JAPANESE,
            prompt=f"Please translate the following text to Japanese:\n\n{element.content}",
            client=client)

try:
    current_message = None # pylint: disable=invalid-name
    threads = []

    while True:
        command = pconsole.input_command("Command: ")

        if command:
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

            elif pstring.equals_ignore_case(command.command, "exit"):
                break

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
