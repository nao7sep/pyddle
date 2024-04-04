# Created: 2024-04-04
# A module that helps us organize knowledge in a tree structure.

import abc
import typing
import uuid

import pyddle_datetime as pdatetime
import pyddle_openai as popenai

class LangTreeElement(abc.ABC):
    def __init__(self, guid=None, creation_utc=None):
        # Shared:
        self.guid = guid if guid is not None else uuid.uuid4()
        self.creation_utc = creation_utc if creation_utc is not None else pdatetime.get_utc_now()

        # For structure:
        self.parent_element_guid = None # May be used like a foreign key.
        self.parent_element: LangTreeElement = None # Not serialized.

    @abc.abstractmethod
    def serialize_to_dict(self):
        pass

class LangTreeMessage(LangTreeElement):
    def __init__(self, guid=None, creation_utc=None, user_role: popenai.OpenAiRole=None, content=None):
        super().__init__(guid=guid, creation_utc=creation_utc)

        # Contents:
        self.user_name = None # "name" alone would be confusing.
        self.user_role: popenai.OpenAiRole = user_role
        self.content = content

        # For structure:
        # Generated usually in this order.
        self.attributes: list[LangTreeAttribute] = []
        self.translations: list[LangTreeTranslation] = []
        self.child_messages: list[LangTreeMessage] = []

    def serialize_to_dict(self):
        dictionary = {}

        # Shared:
        dictionary["guid"] = self.guid
        dictionary["creation_utc"] = pdatetime.utc_to_roundtrip_string(self.creation_utc)
        dictionary["parent_element_guid"] = self.parent_element_guid

        # Contents:
        dictionary["user_name"] = self.user_name
        dictionary["user_role"] = self.user_role.value
        dictionary["content"] = self.content

        # For structure:

        if self.attributes is not None:
            dictionary["attributes"] = [attribute.serialize_to_dict() for attribute in self.attributes]

        if self.translations is not None:
            dictionary["translations"] = [translation.serialize_to_dict() for translation in self.translations]

        if self.child_messages is not None:
            dictionary["child_messages"] = [child_message.serialize_to_dict() for child_message in self.child_messages]

class LangTreeAttribute(LangTreeElement):
    def __init__(self, guid=None, creation_utc=None, name=None, value=None):
        super().__init__(guid=guid, creation_utc=creation_utc)

        # Contents:
        self.name = name
        self.value = value

    def serialize_to_dict(self):
        return {
            # Shared:
            "guid": self.guid,
            "creation_utc": pdatetime.utc_to_roundtrip_string(self.creation_utc),
            "parent_element_guid": self.parent_element_guid,

            # Contents:
            "name": self.name,
            "value": self.value
        }

class LangTreeTranslation(LangTreeElement):
    def __init__(self, guid=None, creation_utc=None, language: typing.Union[popenai.OpenAiLanguage, str]=None, content=None):
        super().__init__(guid=guid, creation_utc=creation_utc)

        # Contents:
        self.language: typing.Union[popenai.OpenAiLanguage, str] = language
        self.content = content

    @property
    def language_str(self):
        if isinstance(self.language, popenai.OpenAiLanguage):
            return self.language.value

        return self.language

    def serialize_to_dict(self):
        return {
            # Shared:
            "guid": self.guid,
            "creation_utc": pdatetime.utc_to_roundtrip_string(self.creation_utc),
            "parent_element_guid": self.parent_element_guid,

            # Contents:
            "language": self.language_str,
            "content": self.content
        }
