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
import pyddle_string # as string
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
        ''' Returns the updated note or None. '''
        for index, existing_note in enumerate(self.notes):
            if existing_note.guid == note.guid:
                self.notes[index] = note
                self.save()
                return note

        return None

    def delete_note_by_guid(self, note):
        ''' Returns the deleted note or None. '''
        for index, existing_note in enumerate(self.notes):
            if existing_note.guid == note.guid:
                del self.notes[index]
                self.save()
                return existing_note

        return None

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
        self.code = None
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
        json_string = json.dumps(self, indent=4, default=serialize_episode)

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

def generate_code():
    return (random.choice(string.ascii_uppercase) +
            random.choice(string.ascii_uppercase) +
            random.choice(string.digits) +
            random.choice(string.digits))

def generate_file_name(code, title):
    # I initially thought about validating the characters in the title, but nobody else would use this script and I would always know what characters to avoid. :)
    return f"{code} {title}.json"

# ------------------------------------------------------------------------------
#     Application
# ------------------------------------------------------------------------------

try:
    kvs_key_prefix = "episodic_trash/"

    episodes_directory_path = kvs.read_from_merged_kvs_data(f"{kvs_key_prefix}episodes_directory_path")
    console.print(f"episodes_directory_path: {episodes_directory_path}")

except Exception:
    console.print_error(traceback.format_exc())

finally:
    debugging.display_press_enter_key_to_continue_if_not_debugging()
