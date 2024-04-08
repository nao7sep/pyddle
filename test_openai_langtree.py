# Created: 2024-04-08
# Tests pyddle_openai_langtree.py.

import json
import traceback

import pyddle_console as pconsole
import pyddle_debugging as pdebugging
import pyddle_global as pglobal
import pyddle_openai as popenai
import pyddle_openai_langtree as plangtree
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

try:
    root_message = plangtree.LangTreeMessage(
        user_role=popenai.OpenAiRole.SYSTEM,
        content="You are a helpful assistant."
    )

    user_message = root_message.create_child_message(
        user_role=popenai.OpenAiRole.USER,
        content="Hello!"
    )

    user_message.create_attribute("title", "Greeting").create_translation(popenai.OpenAiLanguage.JAPANESE, "挨拶")
    user_message.create_translation(popenai.OpenAiLanguage.JAPANESE, "こんにちは！").create_attribute("title", "Greeting in Japanese")

    assistant_message = user_message.generate_child_message()

    new_user_message = assistant_message.create_child_message(
        user_role=popenai.OpenAiRole.USER,
        content="How are you?"
    )

    new_assistant_message = new_user_message.generate_child_message()

    json_str = json.dumps(root_message.serialize_to_dict(), ensure_ascii=False, indent=4)

    pconsole.print("Serialized root message:")
    pconsole.print_lines(pstring.splitlines(json_str), indents=pstring.LEVELED_INDENTS[1])

    new_root_message = plangtree.LangTreeMessage.deserialize_from_dict(json.loads(json_str))
    new_json_str = json.dumps(new_root_message.serialize_to_dict(), ensure_ascii=False, indent=4)

    pconsole.print(f"new_json_str == json_str: {new_json_str == json_str}")

except Exception: # pylint: disable=broad-except
    pconsole.print(traceback.format_exc(), colors=pconsole.ERROR_COLORS)

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
