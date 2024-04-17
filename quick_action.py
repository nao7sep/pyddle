# Created: 2024-04-16
# A simple tool that stores prompts and applies them to the input.

# actions.json contains a few commands and their prompts.
# As the name of the tool should suggest, this is an individual-iteration-only tool that is designed to quickly apply simple, action-oriented prompts to the input.
# If you would like to deepen your knowledge, please consider using langtree.
# This tool is suitable for quick, one-time actions such as translation, refinement, etc.

import json
import os
import sys
import traceback

import pyddle_console as pconsole
import pyddle_datetime as pdatetime
import pyddle_debugging as pdebugging
import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_kvs as pkvs
import pyddle_logging as plogging
import pyddle_openai as popenai
import pyddle_output as poutput
import pyddle_prompts as pprompts
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

class Action:
    def __init__(self, command_, prompt):
        self.command = command_
        self.prompt = prompt

    def serialize_to_dict(self):
        return {
            'command': self.command,
            'prompt': self.prompt,
        }

    @staticmethod
    def deserialize_from_dict(dictionary):
        return Action(
            command_ = dictionary['command'],
            prompt = dictionary['prompt'],
        )

try:
    KVS_KEY_PREFIX = "quick_action/"

    actions_file_path = pkvs.read_from_merged_data(f"{KVS_KEY_PREFIX}actions_file_path")
    pconsole.print(f"actions_file_path: {actions_file_path}")

    actions: list[Action] = []

    def _get_action(command_):
        for action_ in actions:
            if pstring.equals_ignore_case(action_.command, command_):
                return action_

        return None

    def _save():
        pfs.create_parent_directory(actions_file_path)

        with pfs.open_file_and_write_utf_encoding_bom(actions_file_path) as file_:
            json.dump([action.serialize_to_dict() for action in sorted(actions, key = lambda action: action.command)], file_, indent = 4)

    if os.path.isfile(actions_file_path):
        with pfs.open_file_and_detect_utf_encoding(actions_file_path) as file:
            actions.extend([Action.deserialize_from_dict(action_data) for action_data in json.load(file)])

    while True:
        plogging.flush()

        command = pconsole.input_command("Command: ")

        if command:
            if pstring.equals_ignore_case(command.command, "create"):
                new_command = command.get_arg_or_default(0, None)
                new_prompt = command.get_remaining_args_as_str(1) # pylint: disable = invalid-name

                if new_command and new_prompt:
                    if not _get_action(new_command):
                        actions.append(Action(command_ = new_command, prompt = new_prompt))
                        _save()
                        pconsole.print(f"Created: {new_command} ({new_prompt})")

                    else:
                        pconsole.print(f"Already exists: {new_command}", colors = pconsole.ERROR_COLORS)

                    continue

            elif pstring.equals_ignore_case(command.command, "list"):
                if actions:
                    pconsole.print("Actions:")

                    for action in sorted(actions, key = lambda action: action.command):
                        pconsole.print(f"{action.command}: {action.prompt}", indents = pstring.LEVELED_INDENTS[1])

                else:
                    pconsole.print("No actions.")

                continue

            elif pstring.equals_ignore_case(command.command, "update"):
                existing_command = command.get_arg_or_default(0, None)
                new_prompt = command.get_remaining_args_as_str(1) # pylint: disable = invalid-name

                if existing_command and new_prompt:
                    action = _get_action(existing_command)

                    if action:
                        action.prompt = new_prompt
                        _save()
                        pconsole.print(f"Updated: {existing_command} ({new_prompt})")

                    else:
                        pconsole.print(f"Not found: {existing_command}", colors = pconsole.ERROR_COLORS)

                    continue

            elif pstring.equals_ignore_case(command.command, "delete"):
                existing_command = command.get_arg_or_default(0, None)

                if existing_command:
                    action = _get_action(existing_command)

                    if action:
                        actions.remove(action)
                        _save()
                        pconsole.print(f"Deleted: {existing_command}")

                    else:
                        pconsole.print(f"Not found: {existing_command}", colors = pconsole.ERROR_COLORS)

                    continue

            elif specified_action := _get_action(command.command):
                new_text = command.get_remaining_args_as_str(0) # pylint: disable = invalid-name

                if new_text:
                    plogging.log("Input:")

                    plogging.log(f"UTC: {pdatetime.get_utc_now().isoformat()}", indents = pstring.LEVELED_INDENTS[1])
                    plogging.log(f"Prompt: {specified_action.prompt}", indents = pstring.LEVELED_INDENTS[1])
                    plogging.log(f"Text: {new_text}", indents = pstring.LEVELED_INDENTS[1])

                    messages: list[dict[str, str]] = []

                    popenai.add_system_message(messages, pprompts.SYSTEM_MESSAGE_FOR_TEXT_AND_MULTI_SENTENCE_PROMPT_MESSAGES)
                    popenai.add_user_message(messages, pprompts.get_text_message(new_text))
                    popenai.add_user_message(messages, pprompts.get_multi_sentence_prompt_message(specified_action.prompt))

                    response = popenai.create_chat_completions(
                        model = popenai.Model.GPT_4_TURBO,
                        messages = messages,
                        stream = True)

                    if pdebugging.is_debugging():
                        pconsole.print("Messages:")

                        messages_str = json.dumps(messages, ensure_ascii = False, indent = 4)
                        messages_str_lines = pstring.splitlines(messages_str)
                        pconsole.print_lines(messages_str_lines, indents = pstring.LEVELED_INDENTS[1])

                    reader = pstring.ChunkStrReader(pstring.LEVELED_INDENTS[1])

                    pconsole.print("Response:")
                    plogging.log("Output:")

                    for chunk in response:
                        chunk_delta = popenai.extract_first_delta(chunk)

                        if chunk_delta:
                            reader.add_chunk(chunk_delta)

                            chunk_str = reader.read_str()
                            poutput.print_and_log(chunk_str, end = "")
                            sys.stdout.flush()

                    chunk_str = reader.read_str(force = True)
                    end = "" if chunk_str.endswith("\n") else "\n" # pylint: disable = invalid-name
                    poutput.print_and_log(chunk_str, end = end)

                    continue

            elif pstring.equals_ignore_case(command.command, "exit"):
                break

        pconsole.print("Invalid command.", colors = pconsole.ERROR_COLORS)

except Exception: # pylint: disable = broad-except
    pconsole.print(traceback.format_exc(), colors = pconsole.ERROR_COLORS)

finally:
    plogging.flush()

    pdebugging.display_press_enter_key_to_continue_if_not_debugging()
