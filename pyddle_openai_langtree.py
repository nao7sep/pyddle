# Created:
#

from __future__ import annotations
import enum
import pyddle_datetime as dt
import pyddle_openai as openai
from typing import Union
import uuid

# ------------------------------------------------------------------------------
#     Languages
# ------------------------------------------------------------------------------

# The comments have become "episodic" and been moved to: RK32 OpenAI Supported Languages.json

# Probably, this is the only official list of supported languages as of 2024-03-28:
# https://platform.openai.com/docs/guides/text-to-speech
# Shouldnt hurt to start with it, then.

class OpenAiLanguage(enum.Enum):
    AFRIKAANS = "afrikaans"
    ARABIC = "arabic"
    ARMENIAN = "armenian"
    AZERBAIJANI = "azerbaijani"
    BELARUSIAN = "belarusian"
    BOSNIAN = "bosnian"
    BULGARIAN = "bulgarian"
    CATALAN = "catalan"
    CHINESE = "chinese"
    CROATIAN = "croatian"
    CZECH = "czech"
    DANISH = "danish"
    DUTCH = "dutch"
    ENGLISH = "english"
    ESTONIAN = "estonian"
    FINNISH = "finnish"
    FRENCH = "french"
    GALICIAN = "galician"
    GERMAN = "german"
    GREEK = "greek"
    HEBREW = "hebrew"
    HINDI = "hindi"
    HUNGARIAN = "hungarian"
    ICELANDIC = "icelandic"
    INDONESIAN = "indonesian"
    ITALIAN = "italian"
    JAPANESE = "japanese"
    KANNADA = "kannada"
    KAZAKH = "kazakh"
    KOREAN = "korean"
    LATVIAN = "latvian"
    LITHUANIAN = "lithuanian"
    MACEDONIAN = "macedonian"
    MALAY = "malay"
    MARATHI = "marathi"
    MAORI = "maori"
    NEPALI = "nepali"
    NORWEGIAN = "norwegian"
    PERSIAN = "persian"
    POLISH = "polish"
    PORTUGUESE = "portuguese"
    ROMANIAN = "romanian"
    RUSSIAN = "russian"
    SERBIAN = "serbian"
    SLOVAK = "slovak"
    SLOVENIAN = "slovenian"
    SPANISH = "spanish"
    SWAHILI = "swahili"
    SWEDISH = "swedish"
    TAGALOG = "tagalog"
    TAMIL = "tamil"
    THAI = "thai"
    TURKISH = "turkish"
    UKRAINIAN = "ukrainian"
    URDU = "urdu"
    VIETNAMESE = "vietnamese"
    WELSH = "welsh"

# ------------------------------------------------------------------------------
#     Nodes
# ------------------------------------------------------------------------------

class OpenAiBaseNode:
    def __init__(self, role: openai.OpenAiRole, content):
        # Set automatically:
        self.guid = uuid.uuid4()
        self.creation_utc = dt.get_utc_now()

        # Relations:
        # Foreign key.
        # Necessary if the node is stored in a RDBMS.
        self.parent_node_guid = None
        # Wont be serialized; it'd make an infinite loop.
        self._parent_node: OpenAiBaseNode = None
        self.child_nodes: list[OpenAiBaseNode] = []

        # Users must specify:
        self.role: openai.OpenAiRole = role
        self.content = content

        # Optional info:
        # The | thing came out with Python 3.10, which was released in 2021.
        # We should stick to Union just a little longer.
        # https://docs.python.org/3/library/typing.html#typing.Union
        # https://docs.python.org/3/library/stdtypes.html#union-type
        self.language: Union[OpenAiLanguage, str] = None

        # Attributes:
        # Initialized based on the data of the node.
        self.summary = None
        self.title = None

    # I casually wrote about how I like to design CRUD operations.
    # RI31 in FI56 Arguable Design Patterns.json

    def create_child_node(self, child_node: OpenAiBaseNode):
        ''' Returns the child node. '''

        child_node.parent_node_guid = self.guid
        child_node._parent_node = self
        self.child_nodes.append(child_node)
        return child_node

    def update_child_node(self, child_node: OpenAiBaseNode):
        ''' Returns None if the child node was not found. '''

        for index, existing_node in enumerate(self.child_nodes):
            if existing_node.guid == child_node.guid:
                self.child_nodes[index] = child_node
                return child_node

        return None

    def delete_child_node(self, child_node: OpenAiBaseNode):
        ''' Returns None if the child node was not found. '''

        for index, existing_node in enumerate(self.child_nodes):
            if existing_node.guid == child_node.guid:
                del self.child_nodes[index]
                return child_node

        return None

class OpenAiNode(OpenAiBaseNode):
    def __init__(self, role: openai.OpenAiRole, content):
        super().__init__(role=role, content=content)
        self.translations: dict[Union[OpenAiLanguage, str], OpenAiNodeTranslation] = {}

    # And I wrote about these too: PG69 in FI56 Arguable Design Patterns.json

    def create_translation(self, language: Union[OpenAiLanguage, str], translation: OpenAiNodeTranslation):
        ''' Returns the translation. '''

        translation.parent_node_guid = self.guid
        translation._parent_node = self
        self.translations[language] = translation
        return translation

    def update_translation(self, language: Union[OpenAiLanguage, str], translation: OpenAiNodeTranslation):
        ''' Returns None if the translation was not found. '''

        if language in self.translations:
            self.translations[language] = translation
            return translation

        return None

    def delete_translation(self, language: Union[OpenAiLanguage, str]):
        ''' Returns None if the translation was not found. '''

        if language in self.translations:
            del self.translations[language]
            return language

        return None

class OpenAiNodeTranslation(OpenAiBaseNode):
    def __init__(self, role: openai.OpenAiRole, content):
        super().__init__(role=role, content=content)
