# Created: 2024-04-04
# A module that helps us organize knowledge in a tree structure.

import abc
import typing
import uuid

import openai

import pyddle_datetime as pdatetime
import pyddle_openai as popenai

class LangTreeElement(abc.ABC):
    def __init__(self,
                 client: openai.OpenAI=None,
                 chat_settings: popenai.OpenAiChatSettings=None,
                 guid=None,
                 creation_utc=None):

        # Shared settings:
        self.client: openai.OpenAI = client
        self.chat_settings: popenai.OpenAiChatSettings = chat_settings

        # Shared data:
        self.guid = guid if guid is not None else uuid.uuid4()
        self.creation_utc = creation_utc if creation_utc is not None else pdatetime.get_utc_now()

        # For structure:
        self.parent_element_guid = None # May be used like a foreign key.
        self.parent_element: LangTreeElement = None # Not serialized to avoid circular references.

    @abc.abstractmethod
    def serialize_to_dict(self):
        pass

class LangTreeMessage(LangTreeElement):
    def __init__(self,
                 client: openai.OpenAI=None,
                 chat_settings: popenai.OpenAiChatSettings=None,
                 guid=None,
                 creation_utc=None,
                 user_name=None, # Optional, but it's more understandable in this order.
                 user_role: popenai.OpenAiRole=None,
                 content=None):

        super().__init__(client=client, chat_settings=chat_settings, guid=guid, creation_utc=creation_utc)

        # Contents:
        self.user_name = user_name # "name" alone would be confusing.
        self.user_role: popenai.OpenAiRole = user_role
        self.content = content

        # For structure:
        # Generated usually in this order.
        self.attributes: list[LangTreeAttribute] = []
        self.translations: list[LangTreeTranslation] = []
        self.child_messages: list[LangTreeMessage] = []

    def serialize_to_dict(self):
        dictionary = {}

        # Shared data:
        dictionary["guid"] = str(self.guid)
        dictionary["creation_utc"] = pdatetime.utc_to_roundtrip_string(self.creation_utc)
        dictionary["parent_element_guid"] = self.parent_element_guid # None if this is the root.

        # Contents:

        if self.user_name:
            dictionary["user_name"] = self.user_name # Optional.

        dictionary["user_role"] = self.user_role.value
        dictionary["content"] = self.content

        # For structure:
        # Serialized only if they are truthy.

        if self.attributes:
            dictionary["attributes"] = [attribute.serialize_to_dict() for attribute in self.attributes]

        if self.translations:
            dictionary["translations"] = [translation.serialize_to_dict() for translation in self.translations]

        if self.child_messages:
            dictionary["child_messages"] = [child_message.serialize_to_dict() for child_message in self.child_messages]

        return dictionary

class LangTreeAttribute(LangTreeElement):
    def __init__(self,
                 client: openai.OpenAI=None,
                 chat_settings: popenai.OpenAiChatSettings=None,
                 guid=None,
                 creation_utc=None,
                 name=None,
                 value=None):

        super().__init__(client=client, chat_settings=chat_settings, guid=guid, creation_utc=creation_utc)

        # Contents:
        self.name = name
        self.value = value

    def serialize_to_dict(self):
        return {
            # Shared data:
            "guid": str(self.guid),
            "creation_utc": pdatetime.utc_to_roundtrip_string(self.creation_utc),
            "parent_element_guid": self.parent_element_guid,

            # Contents:
            "name": self.name,
            "value": self.value # May be None.
        }

class LangTreeTranslation(LangTreeElement):
    def __init__(self,
                 client: openai.OpenAI=None,
                 chat_settings: popenai.OpenAiChatSettings=None,
                 guid=None,
                 creation_utc=None,
                 language: typing.Union[popenai.OpenAiLanguage, str]=None,
                 content=None):

        super().__init__(client=client, chat_settings=chat_settings, guid=guid, creation_utc=creation_utc)

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
            # Shared data:
            "guid": str(self.guid),
            "creation_utc": pdatetime.utc_to_roundtrip_string(self.creation_utc),
            "parent_element_guid": self.parent_element_guid,

            # Contents:
            "language": self.language_str,
            "content": self.content # Should never be None.
        }
