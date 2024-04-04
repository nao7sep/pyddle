# Created: 2024-04-04
# A module that helps us organize knowledge in a tree structure.

import typing
import uuid

import openai

import pyddle_datetime as pdatetime
import pyddle_openai as popenai

class LangTreeElement:
    def __init__(self,
                 guid=None,
                 creation_utc=None):

        # These are required, but None can be specified to initialize them.
        self.guid = guid if guid is not None else uuid.uuid4()
        self.creation_utc = creation_utc if creation_utc is not None else pdatetime.get_utc_now()

        # Constructor parameters arent prepared for optional things.
        self.parent_element_guid = None # May be used like a foreign key.
        self.parent_element: LangTreeElement = None # Not serialized to avoid circular references.

        # Not serialized; they must be stored somewhere else, perhaps as global settings.
        self.client: openai.OpenAI = None
        self.chat_settings: popenai.OpenAiChatSettings = None
        self.timeout = None

    def serialize_to_dict(self):
        return {
            "guid": str(self.guid),
            "creation_utc": pdatetime.utc_to_roundtrip_string(self.creation_utc),

            "parent_element_guid": self.parent_element_guid
            # "parent_element" is not serialized.
        }

class LangTreeMessage(LangTreeElement):
    def __init__(self,
                 user_role: popenai.OpenAiRole,
                 content,

                 guid=None,
                 creation_utc=None):

        super().__init__(guid=guid, creation_utc=creation_utc)

        # "user_name" is optional and the rest are required.
        # It would be more intuitive to have "user_name" in this order.
        self.user_name = None # "name" alone could be confusing.
        self.user_role: popenai.OpenAiRole = user_role
        self.content = content

        # Generated usually in this order.
        self.attributes: list[LangTreeAttribute] = []
        self.translations: list[LangTreeTranslation] = []
        self.child_messages: list[LangTreeMessage] = []

    def serialize_to_dict(self):
        dictionary = {}

        dictionary.update(super().serialize_to_dict())

        if self.user_name:
            dictionary["user_name"] = self.user_name # Optional.

        dictionary["user_role"] = self.user_role.value
        dictionary["content"] = self.content

        # Serialized only if they are truthy.
        # We dont need a lot of lists where the values are [].

        if self.attributes:
            dictionary["attributes"] = [attribute.serialize_to_dict() for attribute in self.attributes]

        if self.translations:
            dictionary["translations"] = [translation.serialize_to_dict() for translation in self.translations]

        if self.child_messages:
            dictionary["child_messages"] = [child_message.serialize_to_dict() for child_message in self.child_messages]

        return dictionary

class LangTreeAttribute(LangTreeElement):
    def __init__(self,
                 name,
                 value,

                 guid=None,
                 creation_utc=None):

        super().__init__(guid=guid, creation_utc=creation_utc)

        self.name = name
        self.value = value

    def serialize_to_dict(self):
        dictionary = {}

        dictionary.update(super().serialize_to_dict())

        dictionary["name"] = self.name
        dictionary["value"] = self.value # May be None.

        return dictionary

class LangTreeTranslation(LangTreeElement):
    def __init__(self,
                 language: typing.Union[popenai.OpenAiLanguage, str],
                 content,

                 guid=None,
                 creation_utc=None):

        super().__init__(guid=guid, creation_utc=creation_utc)

        self.language: typing.Union[popenai.OpenAiLanguage, str] = language
        self.content = content

    @property
    def language_str(self):
        if isinstance(self.language, popenai.OpenAiLanguage):
            return self.language.value

        return self.language

    def serialize_to_dict(self):
        dictionary = {}

        dictionary.update(super().serialize_to_dict())

        dictionary["language"] = self.language_str
        dictionary["content"] = self.content # Should never be None.

        return dictionary
