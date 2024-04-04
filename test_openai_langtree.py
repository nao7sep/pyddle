# Created: 2024-04-04
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
    # todo: Change to GPT-4 after initial testing.
    chat_settings = popenai.OpenAiChatSettings(popenai.OpenAiModel.GPT_3_5_TURBO)

    root_message = plangtree.LangTreeMessage(
        user_role=popenai.OpenAiRole.SYSTEM,
        content="You are a helpful assistant."
    )

    json_str = json.dumps(root_message.serialize_to_dict(), ensure_ascii=False, indent=4)

    pconsole.print("Serialized root message:")
    pconsole.print_lines(pstring.splitlines(json_str), indents=pstring.LEVELED_INDENTS[1])

except Exception: # pylint: disable=broad-except
    pconsole.print(traceback.format_exc(), colors=pconsole.ERROR_COLORS)

pdebugging.display_press_enter_key_to_continue_if_not_debugging()
