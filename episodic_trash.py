# Created:
#

from abc import ABC, abstractmethod
import enum
import json
import os
import pyddle_console as console
import pyddle_datetime as dt
import pyddle_debugging as debugging
import pyddle_file_system as file_system
import pyddle_json_based_kvs as kvs
import pyddle_path as path
import pyddle_string # as string
import pyperclip
import random
import string
import traceback
import uuid

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
def serialize_episode(episode):
    if isinstance(episode, EpisodeInfo):
        data = {
            "guid": str(episode.guid),
            "creation_utc": dt.utc_to_roundtrip_string(episode.creation_utc),
            "code": episode.code,
            "title": episode.title
        }

        if episode.notes:
            data["notes"] = [serialize_episode(note) for note in episode.notes]

        return data

    elif isinstance(episode, NoteInfo):
        data = {
            "guid": str(episode.guid),
            "creation_utc": dt.utc_to_roundtrip_string(episode.creation_utc),
            "code": episode.code,
            # "parent" and "parent_type" will be restored based on the JSON file's structure.
            "content": pyddle_string.splitlines(episode.content)
        }

        if episode.notes:
            data["notes"] = [serialize_episode(note) for note in episode.notes]

        return data

    else:
        raise RuntimeError(f"Unsupported type: {type(episode)}")

def deserialize_notes(parent, notes_of_parent, note_data):
    for note_data_item in note_data:
        note = NoteInfo()
        note.guid = uuid.UUID(note_data_item["guid"])
        note.creation_utc = dt.roundtrip_string_to_utc(note_data_item["creation_utc"])
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

        notes_of_parent.append(note)

class EpisodeInfo(EntryInfo):
    def __init__(self):
        super().__init__()
        self.title = None
        self.file_path = None

    def load(self):
        if os.path.isfile(self.file_path):
            with file_system.open_file_and_detect_utf_encoding(self.file_path) as episode_file:
                data_from_json = json.load(episode_file)

                self.guid = uuid.UUID(data_from_json["guid"])
                self.creation_utc = dt.roundtrip_string_to_utc(data_from_json["creation_utc"])
                self.code = data_from_json["code"]
                self.title = data_from_json["title"]

                if "notes" in data_from_json:
                    deserialize_notes(self, self.notes, data_from_json["notes"])

    def save(self):
        json_string = json.dumps(self, ensure_ascii=False, indent=4, default=serialize_episode)

        file_system.create_parent_directory(self.file_path)
        file_system.write_all_text_to_file(self.file_path, json_string)

class NoteInfo(EntryInfo):
    def __init__(self):
        super().__init__()
        self.parent = None
        self.parent_type = None
        self.content = None

    def save(self):
        # Calls the parent's save method recursively until it reaches the episode.
        self.parent.save()

def generate_random_code(episodes):
    while True:
        code = (random.choice(string.ascii_uppercase) +
                random.choice(string.ascii_uppercase) +
                random.choice(string.digits) +
                random.choice(string.digits))

        if get_episode(episodes, code):
            continue

        is_note_found = False

        for episode in episodes:
            if get_note(episode.notes, code):
                is_note_found = True
                break

        if is_note_found:
            continue

        return code

# Safer to separate the following 2 functions.

def get_episode(episodes, code):
    for episode in episodes:
        if pyddle_string.equals_ignore_case(episode.code, code):
            return episode

    return None

def get_note(notes, code):
    for note in notes:
        if pyddle_string.equals_ignore_case(note.code, code):
            return note

        if note.notes:
            found_note = get_note(note.notes, code)

            if found_note:
                return found_note

    return None

def generate_file_name(code, title):
    # I initially thought about validating the characters in the title,
    #     but nobody else would use this script and I would always know what characters to avoid. :)
    return f"{code} {title}.json"

# ------------------------------------------------------------------------------
#     Commands
# ------------------------------------------------------------------------------

def episodes_help_command():
    console.print("Commands:")
    console.print("help", indents=pyddle_string.leveledIndents[1])
    console.print("create <title>", indents=pyddle_string.leveledIndents[1])
    console.print("list", indents=pyddle_string.leveledIndents[1])
    console.print("open <code>", indents=pyddle_string.leveledIndents[1])
    console.print("title <code> <title>", indents=pyddle_string.leveledIndents[1])
    console.print("delete <code>", indents=pyddle_string.leveledIndents[1])
    console.print("exit", indents=pyddle_string.leveledIndents[1])

def notes_help_command():
    console.print("Commands:")
    console.print("help", indents=pyddle_string.leveledIndents[1])
    console.print("create <content>", indents=pyddle_string.leveledIndents[1])
    console.print("create copy => Copies content from Clipboard", indents=pyddle_string.leveledIndents[1])
    console.print("child <parent_code> <content>", indents=pyddle_string.leveledIndents[1])
    console.print("child <parent_code> copy => Copies content from Clipboard", indents=pyddle_string.leveledIndents[1])
    console.print("list", indents=pyddle_string.leveledIndents[1])
    console.print("read <code>", indents=pyddle_string.leveledIndents[1])
    console.print("parent <code> <parent_code>", indents=pyddle_string.leveledIndents[1])
    console.print("content <code> <content>", indents=pyddle_string.leveledIndents[1])
    console.print("content <code> copy => Copies content from Clipboard", indents=pyddle_string.leveledIndents[1])
    console.print("delete <code>", indents=pyddle_string.leveledIndents[1])
    console.print("close", indents=pyddle_string.leveledIndents[1])

def episodes_list_command(episodes):
    console.print("Episodes:")

    # Sorted like a directory's file list.
    for episode in sorted(episodes, key=lambda episode: episode.title.lower()):
        console.print(f"{episode.code} {episode.title}", indents=pyddle_string.leveledIndents[1])

def notes_list_command(notes, depth):
    if depth == 0:
        console.print("Notes:")

    for note in notes:
        partial_content = pyddle_string.splitlines(note.content)[0] # For a start, experimentally.
        console.print(f"{note.code} {partial_content}", indents=pyddle_string.leveledIndents[depth + 1])

        if note.notes:
            notes_list_command(note.notes, depth + 1)

def episodes_open_command(episodes, command):
    code = command.get_arg_or_default(0, None)

    if code:
        episode = get_episode(episodes, code)

        if episode:
            while True:
                command = console.input_command(f"Episode {episode.code}: ")

                if command:
                    if pyddle_string.equals_ignore_case(command.command, "help"):
                        notes_help_command()

                    elif pyddle_string.equals_ignore_case(command.command, "create"):
                        content = command.get_remaining_args_as_str(0)

                        if pyddle_string.equals_ignore_case(content, "copy"):
                            try:
                                content = pyperclip.paste()

                            except Exception:
                                console.print_error("Failed to copy content.")
                                continue

                        if content:
                            note = NoteInfo()
                            note.guid = uuid.uuid4()
                            note.creation_utc = dt.get_utc_now()
                            note.code = generate_random_code(episodes)
                            note.parent = episode
                            note.parent_type = ParentType.EPISODE
                            note.content = content

                            try:
                                episode.create_note(note)

                            except Exception:
                                console.print_error("Failed to create note.")
                                continue

                            console.print("Note created.")

                        else:
                            console.print_error("Content is required.")

                    elif pyddle_string.equals_ignore_case(command.command, "child"):
                        parent_code = command.get_arg_or_default(0, None)

                        if parent_code:
                            parent_note = get_note(episode.notes, parent_code)

                            if parent_note:
                                content = command.get_remaining_args_as_str(1)

                                if pyddle_string.equals_ignore_case(content, "copy"):
                                    try:
                                        content = pyperclip.paste()

                                    except Exception:
                                        console.print_error("Failed to copy content.")
                                        continue

                                if content:
                                    note = NoteInfo()
                                    note.guid = uuid.uuid4()
                                    note.creation_utc = dt.get_utc_now()
                                    note.code = generate_random_code(episodes)
                                    note.parent = parent_note
                                    note.parent_type = ParentType.NOTE
                                    note.content = content

                                    try:
                                        parent_note.create_note(note)

                                    except Exception:
                                        console.print_error("Failed to create note.")
                                        continue

                                    console.print("Note created.")

                                else:
                                    console.print_error("Content is required.")

                            else:
                                console.print_error("Parent note not found.")

                        else:
                            console.print_error("Parent code is required.")

                    elif pyddle_string.equals_ignore_case(command.command, "list"):
                        notes_list_command(episode.notes, depth=0)

                    elif pyddle_string.equals_ignore_case(command.command, "read"):
                        code = command.get_arg_or_default(0, None)

                        if code:
                            note = get_note(episode.notes, code)

                            if note:
                                console.print("Content:")
                                console.print(note.content, indents=pyddle_string.leveledIndents[1])

                            else:
                                console.print_error("Note not found.")

                        else:
                            console.print_error("Code is required.")

                    elif pyddle_string.equals_ignore_case(command.command, "parent"):
                        code = command.get_arg_or_default(0, None)

                        if code:
                            note = get_note(episode.notes, code)

                            if note:
                                parent_code = command.get_arg_or_default(1, None)

                                if parent_code:
                                    parent_note = get_note(episode.notes, parent_code)

                                    if parent_note:
                                        old_parent = note.parent
                                        note.parent = parent_note

                                        old_parent_type = note.parent_type
                                        note.parent_type = ParentType.NOTE

                                        try:
                                            parent_note.create_note(note)
                                            old_parent.delete_note(note)

                                        except Exception:
                                            try:
                                                if get_note(parent_note.notes, note.code):
                                                    parent_note.delete_note(note)

                                            except Exception:
                                                pass

                                            note.parent = old_parent
                                            note.parent_type = old_parent_type
                                            # The old parent should still contain the note.

                                            console.print_error("Failed to update parent.")

                                            continue

                                        console.print("Parent updated.")

                                    else:
                                        console.print_error("Parent note not found.")

                                else:
                                    console.print_error("Parent code is required.")

                            else:
                                console.print_error("Note not found.")

                        else:
                            console.print_error("Code is required.")

                    elif pyddle_string.equals_ignore_case(command.command, "content"):
                        code = command.get_arg_or_default(0, None)

                        if code:
                            note = get_note(episode.notes, code)

                            if note:
                                content = command.get_remaining_args_as_str(1)

                                if pyddle_string.equals_ignore_case(content, "copy"):
                                    try:
                                        content = pyperclip.paste()

                                    except Exception:
                                        console.print_error("Failed to copy content.")
                                        continue

                                if content:
                                    old_content = note.content
                                    note.content = content

                                    try:
                                        note.parent.update_note(note)

                                    except Exception:
                                        note.content = old_content
                                        console.print_error("Failed to update content.")
                                        continue

                                    console.print("Content updated.")

                                else:
                                    console.print_error("Content is required.")

                            else:
                                console.print_error("Note not found.")

                        else:
                            console.print_error("Code is required.")

                    elif pyddle_string.equals_ignore_case(command.command, "delete"):
                        code = command.get_arg_or_default(0, None)

                        if code:
                            note = get_note(episode.notes, code)

                            if note:
                                try:
                                    note.parent.delete_note(note)

                                except Exception:
                                    console.print_error(f"Failed to delete note: {note.code}")
                                    continue

                                console.print("Note deleted.")

                            else:
                                console.print_error("Note not found.")

                        else:
                            console.print_error("Code is required.")

                    elif pyddle_string.equals_ignore_case(command.command, "close"):
                        break

                    else:
                        console.print_error("Invalid command.")

                else:
                    console.print_error("Command is required.")

        else:
            console.print_error("Episode not found.")

    else:
        console.print_error("Code is required.")

# ------------------------------------------------------------------------------
#     Application
# ------------------------------------------------------------------------------

try:
    kvs_key_prefix = "episodic_trash/"

    episodes_directory_path = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}episodes_directory_path")
    console.print(f"episodes_directory_path: {episodes_directory_path}")

    episodes = []

    if os.path.isdir(episodes_directory_path):
        for episode_file_name in os.listdir(episodes_directory_path):
            _, extension = os.path.splitext(episode_file_name)

            if pyddle_string.equals_ignore_case(extension, ".json"):
                try:
                    episode = EpisodeInfo()
                    episode.file_path = os.path.join(episodes_directory_path, episode_file_name)
                    episode.load()
                    episodes.append(episode)

                except Exception as exception:
                    console.print_error(f"Invalid episode file: {episode_file_name}")

    if episodes:
        episodes_list_command(episodes)

    else:
        console.print("No episodes found.")
        episodes_help_command()

    while True:
        command = console.input_command("Command: ")

        if command:
            if pyddle_string.equals_ignore_case(command.command, "help"):
                episodes_help_command()

            elif pyddle_string.equals_ignore_case(command.command, "create"):
                title = command.get_remaining_args_as_str(0)

                if title:
                    if path.contains_invalid_file_name_chars(title):
                        console.print_error("Title contains invalid characters.")
                        continue

                    episode = EpisodeInfo()
                    episode.guid = uuid.uuid4()
                    episode.creation_utc = dt.get_utc_now()
                    episode.code = generate_random_code(episodes)
                    episode.title = title
                    episode.file_path = os.path.join(episodes_directory_path, generate_file_name(code, title))

                    try:
                        episode.save()

                    except Exception:
                        console.print_error(f"Failed to create episode: {title}")
                        continue

                    episodes.append(episode)

                    console.print("Episode created.")

                else:
                    console.print_error("Title is required.")

            elif pyddle_string.equals_ignore_case(command.command, "list"):
                episodes_list_command(episodes)

            elif pyddle_string.equals_ignore_case(command.command, "open"):
                episodes_open_command(episodes, command)

            elif pyddle_string.equals_ignore_case(command.command, "title"):
                code = command.get_arg_or_default(0, None)

                if code:
                    episode = get_episode(episodes, code)

                    if episode:
                        title = command.get_remaining_args_as_str(1)

                        if title:
                            if path.contains_invalid_file_name_chars(title):
                                console.print_error("Title contains invalid characters.")
                                continue

                            old_title = episode.title
                            episode.title = title

                            old_file_path = episode.file_path
                            episode.file_path = os.path.join(episodes_directory_path, generate_file_name(episode.code, title))

                            try:
                                episode.save()
                                os.remove(old_file_path)

                            except Exception:
                                try:
                                    if os.path.isfile(episode.file_path):
                                        os.remove(episode.file_path)

                                except Exception:
                                    pass

                                episode.title = old_title
                                episode.file_path = old_file_path
                                # The old file should still exist.

                                console.print_error(f"Failed to update title: {title}")

                                continue

                            console.print("Title updated.")

                        else:
                            console.print_error("Title is required.")

                    else:
                        console.print_error("Episode not found.")

                else:
                    console.print_error("Code is required.")

            elif pyddle_string.equals_ignore_case(command.command, "delete"):
                code = command.get_arg_or_default(0, None)

                if code:
                    episode = get_episode(episodes, code)

                    if episode:
                        try:
                            os.remove(episode.file_path)

                        except Exception:
                            console.print_error(f"Failed to delete episode: {episode.title}")
                            continue

                        episodes.remove(episode)

                        console.print("Episode deleted.")

                    else:
                        console.print_error("Episode not found.")

                else:
                    console.print_error("Code is required.")

            elif pyddle_string.equals_ignore_case(command.command, "exit"):
                break

            else:
                console.print_error("Invalid command.")

        else:
            console.print_error("Command is required.")

except Exception:
    console.print_error(traceback.format_exc())

finally:
    debugging.display_press_enter_key_to_continue_if_not_debugging()
