# Created:
# A module that helps us organize knowledge in a tree structure.

import typing
import uuid

import openai

import pyddle_datetime as pdatetime
import pyddle_openai as popenai

class LangTreeElement:
    def __init__(
            self,

            guid=None,
            creation_utc=None):

        self.guid = guid if guid is not None else uuid.uuid4()
        self.creation_utc = creation_utc if creation_utc is not None else pdatetime.get_utc_now()

        self.parent_element_guid = None
        self.parent_element: LangTreeElement = None

        self.attributes: dict[str, LangTreeAttribute] = {}
        self.translations: dict[typing.Union[popenai.OpenAiLanguage, str], LangTreeTranslation] = {}

        self.client: openai.OpenAI = None
        self.chat_settings: popenai.OpenAiChatSettings = None
        self.timeout = None

    def serialize_to_dict(self):
        dictionary = {}

        dictionary["guid"] = str(self.guid)
        dictionary["creation_utc"] = pdatetime.utc_to_roundtrip_string(self.creation_utc)

        dictionary["parent_element_guid"] = str(self.parent_element_guid) if self.parent_element_guid is not None else None

        if self.attributes:
            dictionary["attributes"] = [attribute.serialize_to_dict() for attribute in self.attributes.values()]

        if self.translations:
            dictionary["translations"] = [translation.serialize_to_dict() for translation in self.translations.values()]

        return dictionary

class LangTreeMessage(LangTreeElement):
    def __init__(
            self,

            user_role: popenai.OpenAiRole,
            content,

            guid=None,
            creation_utc=None):

        super().__init__(
            guid=guid,
            creation_utc=creation_utc)

        self.user_name = None
        self.user_role: popenai.OpenAiRole = user_role
        self.content = content

        self.child_messages: list[LangTreeMessage] = []

    def serialize_to_dict(self):
        dictionary = {}

        dictionary.update(super().serialize_to_dict())

        if self.user_name:
            dictionary["user_name"] = self.user_name

        dictionary["user_role"] = self.user_role.value
        dictionary["content"] = self.content

        if self.child_messages:
            dictionary["child_messages"] = [child_message.serialize_to_dict() for child_message in self.child_messages]

        return dictionary

class LangTreeAttribute(LangTreeElement):
    def __init__(
            self,

            name,
            value,

            guid=None,
            creation_utc=None):

        super().__init__(
            guid=guid,
            creation_utc=creation_utc)

        self.name = name
        self.value = value

    def serialize_to_dict(self):
        dictionary = {}

        dictionary.update(super().serialize_to_dict())

        dictionary["name"] = self.name
        dictionary["value"] = self.value

        return dictionary

class LangTreeTranslation(LangTreeElement):
    def __init__(
            self,

            language: typing.Union[popenai.OpenAiLanguage, str],
            content,

            guid=None,
            creation_utc=None):

        super().__init__(
            guid=guid,
            creation_utc=creation_utc)

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
        dictionary["content"] = self.content

        return dictionary
