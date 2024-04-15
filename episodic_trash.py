# Created: 2024-03-24
# A personal tool to manage "episodic comments" moved from source code.

from abc import ABC, abstractmethod
import enum
import json
import os
import random
import string
import traceback
import typing
import uuid

import pyperclip # type: ignore

import pyddle_console as pconsole
import pyddle_datetime as pdatetime
import pyddle_debugging as pdebugging
import pyddle_file_system as pfs
import pyddle_global as pglobal
import pyddle_kvs as pkvs
import pyddle_path as ppath
import pyddle_string as pstring

pglobal.set_main_script_file_path(__file__)

# ------------------------------------------------------------------------------
#     Classes and functions
# ------------------------------------------------------------------------------

class ParentType(enum.Enum):
    EPISODE = 1
    NOTE = 2

class EntryInfo(ABC):
    def __init__(self):
        self.guid = None
        self.creation_utc = None
        self.code = None
        self.notes = []

    @abstractmethod
    def save(self):
        pass

    def create_note(self, note):
        ''' Returns the created note. '''

        self.notes.append(note)
        self.save()
        return note

    def update_note(self, note):
        ''' Raises an exception if the note is not found. '''

        for index, existing_note in enumerate(self.notes):
            if existing_note.guid == note.guid:
                self.notes[index] = note
                self.save()
                return note

        raise RuntimeError(f"Note not found: {note.guid}")

    def delete_note(self, note):
        ''' Raises an exception if the note is not found. '''

        for index, existing_note in enumerate(self.notes):
            if existing_note.guid == note.guid:
                del self.notes[index]
                self.save()
                return existing_note

        raise RuntimeError(f"Note not found: {note.guid}")

# This method can also serialize notes.
def serialize_episode(episode_):
    if isinstance(episode_, EpisodeInfo):
        data = {
            "guid": str(episode_.guid),
            "creation_utc": pdatetime.utc_to_roundtrip_string(episode_.creation_utc),
            "code": episode_.code,
            "title": episode_.title
        }

        if episode_.notes:
            data["notes"] = [serialize_episode(note) for note in sorted(episode_.notes, key = lambda note: note.creation_utc)]

        return data

    elif isinstance(episode_, NoteInfo):
        data = {
            "guid": str(episode_.guid),
            "creation_utc": pdatetime.utc_to_roundtrip_string(episode_.creation_utc),
            "code": episode_.code,
            # "parent" and "parent_type" will be restored based on the JSON file's structure.
            "content": pstring.splitlines(episode_.content)
        }

        if episode_.notes:
            data["notes"] = [serialize_episode(note) for note in sorted(episode_.notes, key = lambda note: note.creation_utc)]

        return data

    else:
        raise RuntimeError(f"Unsupported type: {type(episode_)}")

def deserialize_notes(parent, notes_of_parent, note_data):
    for note_data_item in note_data:
        note = NoteInfo()
        note.guid = uuid.UUID(note_data_item["guid"])
        note.creation_utc = pdatetime.roundtrip_string_to_utc(note_data_item["creation_utc"])
        note.code = note_data_item["code"]
        note.parent = parent

        if isinstance(parent, EpisodeInfo):
            note.parent_type = ParentType.EPISODE

        elif isinstance(parent, NoteInfo):
            note.parent_type = ParentType.NOTE

        else:
            raise RuntimeError(f"Unsupported type: {type(parent)}")

        note.content = "\n".join(note_data_item["content"])

        if "notes" in note_data_item:
            deserialize_notes(note, note.notes, note_data_item["notes"])
            note.notes.sort(key = lambda note: note.creation_utc)

        notes_of_parent.append(note)

class EpisodeInfo(EntryInfo):
    def __init__(self):
        super().__init__()
        self.title = None
        self.file_path: str | None = None

    def load(self):
        if self.file_path and os.path.isfile(self.file_path):
            with pfs.open_file_and_detect_utf_encoding(self.file_path) as episode_file:
                data_from_json = json.load(episode_file)

                self.guid = uuid.UUID(data_from_json["guid"])
                self.creation_utc = pdatetime.roundtrip_string_to_utc(data_from_json["creation_utc"])
                self.code = data_from_json["code"]
                self.title = data_from_json["title"]

                if "notes" in data_from_json:
                    deserialize_notes(self, self.notes, data_from_json["notes"])
                    self.notes.sort(key = lambda note: note.creation_utc)

    def save(self):
        json_string = json.dumps(self, ensure_ascii = False, indent = 4, default = serialize_episode)

        pfs.create_parent_directory(self.file_path)
        pfs.write_all_text_to_file(self.file_path, json_string)

class NoteInfo(EntryInfo):
    def __init__(self):
        super().__init__()
        self.parent = None
        self.parent_type = None
        self.content = None

    def save(self):
        # Calls the parent's save method recursively until it reaches the episode.
        typing.cast(EntryInfo, self.parent).save()

def generate_random_code(episodes_):
    while True:
        code_ = (random.choice(string.ascii_uppercase) +
                random.choice(string.ascii_uppercase) +
                random.choice(string.digits) +
                random.choice(string.digits))

        if get_episode(episodes_, code_):
            continue

        is_note_found = False

        for episode_ in episodes_:
            if get_note(episode_.notes, code_):
                is_note_found = True
                break

        if is_note_found:
            continue

        return code_

# Safer to separate the following 2 functions.

def get_episode(episodes_, code_):
    for episode_ in episodes_:
        if pstring.equals_ignore_case(episode_.code, code_):
            return episode_

    return None

def get_note(notes, code_):
    for note in notes:
        if pstring.equals_ignore_case(note.code, code_):
            return note

        if note.notes:
            found_note = get_note(note.notes, code_)

            if found_note:
                return found_note

    return None

def generate_file_name(code_, title_):
    # I initially thought about validating the characters in the title,
    #     but nobody else would use this script and I would always know what characters to avoid. :)
    return f"{code_} {title_}.json"

# ------------------------------------------------------------------------------
#     Commands
# ------------------------------------------------------------------------------

def episodes_help_command():
    pconsole.print("Commands:")
    pconsole.print("help", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("create <title>", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("list", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("open <code>", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("title <code> <title>", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("delete <code>", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("exit", indents = pstring.LEVELED_INDENTS[1])

def notes_help_command():
    pconsole.print("Commands:")
    pconsole.print("help", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("create <content>", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("create copy => Copies content from Clipboard", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("child <parent_code> <content>", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("child <parent_code> copy => Copies content from Clipboard", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("list", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("read <code>", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("parent <code> <parent_code>", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("content <code> <content>", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("content <code> copy => Copies content from Clipboard", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("delete <code>", indents = pstring.LEVELED_INDENTS[1])
    pconsole.print("close", indents = pstring.LEVELED_INDENTS[1])

def episodes_list_command(episodes_):
    pconsole.print("Episodes:")

    if not episodes_:
        pconsole.print("No episodes found.", indents = pstring.LEVELED_INDENTS[1])
        return

    # Sorted like a directory's file list.
    for episode_ in sorted(episodes_, key = lambda episode: episode.title.lower()):
        pconsole.print(f"{episode_.code} {episode_.title}", indents = pstring.LEVELED_INDENTS[1])

def notes_list_command(notes, depth):
    if depth == 0:
        pconsole.print("Notes:")

        if not notes:
            pconsole.print("No notes found.", indents = pstring.LEVELED_INDENTS[1])
            return

    for note in notes:
        partial_content = pstring.splitlines(note.content)[0] # For a start, experimentally.
        pconsole.print(f"{note.code} {partial_content}", indents = pstring.LEVELED_INDENTS[depth + 1])

        if note.notes:
            notes_list_command(note.notes, depth + 1)

def episodes_open_command(episodes_, command_):
    code_ = command_.get_arg_or_default(0, None)

    if code_:
        episode_ = get_episode(episodes_, code_)

        if episode_:
            if not episode_.notes:
                notes_help_command()

            while True:
                notes_list_command(episode_.notes, depth = 0)

                command_ = pconsole.input_command(f"Episode {episode_.code}: ")

                if command_:
                    if pstring.equals_ignore_case(command_.command, "help"):
                        notes_help_command()

                    elif pstring.equals_ignore_case(command_.command, "create"):
                        content = pstring.normalize_singleline_str(command_.get_remaining_args_as_str(0))

                        if pstring.equals_ignore_case(content, "copy"):
                            try:
                                content = pstring.normalize_multiline_str(pyperclip.paste())

                            except Exception: # pylint: disable = broad-except
                                pconsole.print("Failed to copy content.", colors = pconsole.ERROR_COLORS)
                                continue

                        if content:
                            note = NoteInfo()
                            note.guid = uuid.uuid4()
                            note.creation_utc = pdatetime.get_utc_now()
                            note.code = generate_random_code(episodes_)
                            note.parent = episode_
                            note.parent_type = ParentType.EPISODE
                            note.content = content

                            try:
                                episode_.create_note(note)

                            except Exception: # pylint: disable = broad-except
                                pconsole.print("Failed to create note.", colors = pconsole.ERROR_COLORS)
                                continue

                            pconsole.print("Note created.")

                        else:
                            pconsole.print("Content is required.", colors = pconsole.ERROR_COLORS)

                    elif pstring.equals_ignore_case(command_.command, "child"):
                        parent_code = command_.get_arg_or_default(0, None)

                        if parent_code:
                            parent_note = get_note(episode_.notes, parent_code)

                            if parent_note:
                                content = pstring.normalize_singleline_str(command_.get_remaining_args_as_str(1))

                                if pstring.equals_ignore_case(content, "copy"):
                                    try:
                                        content = pstring.normalize_multiline_str(pyperclip.paste())

                                    except Exception: # pylint: disable = broad-except
                                        pconsole.print("Failed to copy content.", colors = pconsole.ERROR_COLORS)
                                        continue

                                if content:
                                    note = NoteInfo()
                                    note.guid = uuid.uuid4()
                                    note.creation_utc = pdatetime.get_utc_now()
                                    note.code = generate_random_code(episodes_)
                                    note.parent = parent_note
                                    note.parent_type = ParentType.NOTE
                                    note.content = content

                                    try:
                                        parent_note.create_note(note)

                                    except Exception: # pylint: disable = broad-except
                                        pconsole.print("Failed to create note.", colors = pconsole.ERROR_COLORS)
                                        continue

                                    pconsole.print("Note created.")

                                else:
                                    pconsole.print("Content is required.", colors = pconsole.ERROR_COLORS)

                            else:
                                pconsole.print("Parent note not found.", colors = pconsole.ERROR_COLORS)

                        else:
                            pconsole.print("Parent code is required.", colors = pconsole.ERROR_COLORS)

                    elif pstring.equals_ignore_case(command_.command, "list"):
                        notes_list_command(episode_.notes, depth = 0)

                    elif pstring.equals_ignore_case(command_.command, "read"):
                        code_ = command_.get_arg_or_default(0, None)

                        if code_:
                            note = get_note(episode_.notes, code_)

                            if note:
                                pconsole.print("Content:")

                                for line in pstring.splitlines(note.content):
                                    pconsole.print(line, indents = pstring.LEVELED_INDENTS[1])

                            else:
                                pconsole.print("Note not found.", colors = pconsole.ERROR_COLORS)

                        else:
                            pconsole.print("Code is required.", colors = pconsole.ERROR_COLORS)

                    elif pstring.equals_ignore_case(command_.command, "parent"):
                        code_ = command_.get_arg_or_default(0, None)

                        if code_:
                            note = get_note(episode_.notes, code_)

                            if note:
                                parent_code = command_.get_arg_or_default(1, None)

                                if parent_code:
                                    parent_note = get_note(episode_.notes, parent_code)

                                    if parent_note:
                                        old_parent = note.parent
                                        note.parent = parent_note

                                        old_parent_type = note.parent_type
                                        note.parent_type = ParentType.NOTE

                                        try:
                                            parent_note.create_note(note)
                                            parent_note.notes.sort(key = lambda note: note.creation_utc)
                                            typing.cast(EntryInfo, old_parent).delete_note(note)

                                        except Exception: # pylint: disable = broad-except
                                            try:
                                                if get_note(parent_note.notes, note.code):
                                                    parent_note.delete_note(note)

                                            except Exception: # pylint: disable = broad-except
                                                pass

                                            note.parent = old_parent
                                            note.parent_type = old_parent_type
                                            # The old parent should still contain the note.

                                            pconsole.print("Failed to update parent.", colors = pconsole.ERROR_COLORS)

                                            continue

                                        pconsole.print("Parent updated.")

                                    else:
                                        pconsole.print("Parent note not found.", colors = pconsole.ERROR_COLORS)

                                else:
                                    pconsole.print("Parent code is required.", colors = pconsole.ERROR_COLORS)

                            else:
                                pconsole.print("Note not found.", colors = pconsole.ERROR_COLORS)

                        else:
                            pconsole.print("Code is required.", colors = pconsole.ERROR_COLORS)

                    elif pstring.equals_ignore_case(command_.command, "content"):
                        code_ = command_.get_arg_or_default(0, None)

                        if code_:
                            note = get_note(episode_.notes, code_)

                            if note:
                                content = pstring.normalize_singleline_str(command_.get_remaining_args_as_str(1))

                                if pstring.equals_ignore_case(content, "copy"):
                                    try:
                                        content = pstring.normalize_multiline_str(pyperclip.paste())

                                    except Exception: # pylint: disable = broad-except
                                        pconsole.print("Failed to copy content.", colors = pconsole.ERROR_COLORS)
                                        continue

                                if content:
                                    old_content = note.content
                                    note.content = content

                                    try:
                                        typing.cast(EntryInfo, note.parent).update_note(note)

                                    except Exception: # pylint: disable = broad-except
                                        note.content = old_content
                                        pconsole.print("Failed to update content.", colors = pconsole.ERROR_COLORS)
                                        continue

                                    pconsole.print("Content updated.")

                                else:
                                    pconsole.print("Content is required.", colors = pconsole.ERROR_COLORS)

                            else:
                                pconsole.print("Note not found.", colors = pconsole.ERROR_COLORS)

                        else:
                            pconsole.print("Code is required.", colors = pconsole.ERROR_COLORS)

                    elif pstring.equals_ignore_case(command_.command, "delete"):
                        code_ = command_.get_arg_or_default(0, None)

                        if code_:
                            note = get_note(episode_.notes, code_)

                            if note:
                                try:
                                    typing.cast(EntryInfo, note.parent).delete_note(note)

                                except Exception: # pylint: disable = broad-except
                                    pconsole.print("Failed to delete note.", colors = pconsole.ERROR_COLORS)
                                    continue

                                pconsole.print("Note deleted.")

                            else:
                                pconsole.print("Note not found.", colors = pconsole.ERROR_COLORS)

                        else:
                            pconsole.print("Code is required.", colors = pconsole.ERROR_COLORS)

                    elif pstring.equals_ignore_case(command_.command, "close"):
                        break

                    else:
                        pconsole.print("Invalid command.", colors = pconsole.ERROR_COLORS)

                else:
                    pconsole.print("Command is required.", colors = pconsole.ERROR_COLORS)

        else:
            pconsole.print("Episode not found.", colors = pconsole.ERROR_COLORS)

    else:
        pconsole.print("Code is required.", colors = pconsole.ERROR_COLORS)

# ------------------------------------------------------------------------------
#     Application
# ------------------------------------------------------------------------------

try:
    KVS_KEY_PREFIX = "episodic_trash/"

    episodic_directory_path = pkvs.read_from_merged_kvs_data(f"{KVS_KEY_PREFIX}episodic_directory_path")
    pconsole.print(f"episodic_directory_path: {episodic_directory_path}")

    episodes = []

    if os.path.isdir(episodic_directory_path):
        for episode_file_name in os.listdir(episodic_directory_path):
            _, extension = os.path.splitext(episode_file_name)

            if pstring.equals_ignore_case(extension, ".json"):
                try:
                    episode = EpisodeInfo()
                    episode.file_path = os.path.join(episodic_directory_path, episode_file_name)
                    episode.load()
                    episodes.append(episode)

                except Exception as exception: # pylint: disable = broad-except
                    pconsole.print(f"Invalid episode file: {episode_file_name}", colors = pconsole.ERROR_COLORS)

    if not episodes:
        episodes_help_command()

    while True:
        episodes_list_command(episodes)

        command = pconsole.input_command("Command: ")

        if command:
            if pstring.equals_ignore_case(command.command, "help"):
                episodes_help_command()

            elif pstring.equals_ignore_case(command.command, "create"):
                title = pstring.normalize_singleline_str(command.get_remaining_args_as_str(0))

                if title:
                    if ppath.contains_invalid_file_name_chars(title):
                        pconsole.print("Title contains invalid characters.", colors = pconsole.ERROR_COLORS)
                        continue

                    episode = EpisodeInfo()
                    episode.guid = uuid.uuid4()
                    episode.creation_utc = pdatetime.get_utc_now()
                    episode.code = generate_random_code(episodes)
                    episode.title = title
                    episode.file_path = os.path.join(episodic_directory_path, generate_file_name(episode.code, title))

                    try:
                        episode.save()

                    except Exception: # pylint: disable = broad-except
                        pconsole.print("Failed to create episode.", colors = pconsole.ERROR_COLORS)
                        continue

                    episodes.append(episode)

                    pconsole.print("Episode created.")

                else:
                    pconsole.print("Title is required.", colors = pconsole.ERROR_COLORS)

            elif pstring.equals_ignore_case(command.command, "list"):
                episodes_list_command(episodes)

            elif pstring.equals_ignore_case(command.command, "open"):
                episodes_open_command(episodes, command)

            elif pstring.equals_ignore_case(command.command, "title"):
                code = command.get_arg_or_default(0, None)

                if code:
                    episode = get_episode(episodes, code)

                    if episode:
                        title = pstring.normalize_singleline_str(command.get_remaining_args_as_str(1))

                        if title:
                            if ppath.contains_invalid_file_name_chars(title):
                                pconsole.print("Title contains invalid characters.", colors = pconsole.ERROR_COLORS)
                                continue

                            old_title = episode.title
                            episode.title = title

                            old_file_path = episode.file_path
                            episode.file_path = os.path.join(episodic_directory_path, generate_file_name(episode.code, title))

                            try:
                                episode.save()
                                os.remove(typing.cast(str, old_file_path))

                            except Exception: # pylint: disable = broad-except
                                try:
                                    if episode.file_path:
                                        if os.path.isfile(episode.file_path):
                                            os.remove(episode.file_path)

                                except Exception: # pylint: disable = broad-except
                                    pass

                                episode.title = old_title
                                episode.file_path = old_file_path
                                # The old file should still exist.

                                pconsole.print("Failed to update title.", colors = pconsole.ERROR_COLORS)

                                continue

                            pconsole.print("Title updated.")

                        else:
                            pconsole.print("Title is required.", colors = pconsole.ERROR_COLORS)

                    else:
                        pconsole.print("Episode not found.", colors = pconsole.ERROR_COLORS)

                else:
                    pconsole.print("Code is required.", colors = pconsole.ERROR_COLORS)

            elif pstring.equals_ignore_case(command.command, "delete"):
                code = command.get_arg_or_default(0, None)

                if code:
                    episode = get_episode(episodes, code)

                    if episode:
                        try:
                            os.remove(typing.cast(str, episode.file_path))

                        except Exception: # pylint: disable = broad-except
                            pconsole.print("Failed to delete episode.", colors = pconsole.ERROR_COLORS)
                            continue

                        episodes.remove(episode)

                        pconsole.print("Episode deleted.")

                    else:
                        pconsole.print("Episode not found.", colors = pconsole.ERROR_COLORS)

                else:
                    pconsole.print("Code is required.", colors = pconsole.ERROR_COLORS)

            elif pstring.equals_ignore_case(command.command, "exit"):
                break

            else:
                pconsole.print("Invalid command.", colors = pconsole.ERROR_COLORS)

        else:
            pconsole.print("Command is required.", colors = pconsole.ERROR_COLORS)

except Exception: # pylint: disable = broad-except
    pconsole.print(traceback.format_exc(), colors = pconsole.ERROR_COLORS)

finally:
    pdebugging.display_press_enter_key_to_continue_if_not_debugging()
