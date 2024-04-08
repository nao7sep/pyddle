# Created:
# A module that helps us organize knowledge in a tree structure.

import typing
import uuid

import openai

import pyddle_datetime as pdatetime
import pyddle_openai as popenai

# Some common practice for this module:
#     * Required fields are included in the constructor (even if they are inherited; for clarity)
#     * Some required fields have None as a default value,
#           indicating they will be initialized internally OR default instances will be used
#     * For "client", "chat_settings" and "timeout",
#           1) Parameter values, 2) Class field values, 3) Default values (some of which are lazy loaded) are used in this order
#     * The classes are far from thread-safe, but each element, if accessed exclusively, should be thread-safe
#           => Meaning we should be able to auto-generate attributes and translations in parallel
#     * Methods that access the AI to have things generated,
#           must NOT damage the data structure if the operation fails and an exception is raised
#           => Fields must be updated only at the very end of the operation
#     * As nobody wants to wait for every API call to generate the entire response,
#           1) For messages, we implement waiting (slow) methods and chunk streaming methods,
#           2) For attributes and translations, we keep the classes open and leave room for future async methods
#     * Attributes must be extensible => Explained later
#     * Class fields that would cause circular references are not serialized

# I initially thought about "title" and "description" or "summary" as required attributes.
# But if I do so and occasionally require the latter to construct the context for each API call,
#     these fields will have to coexist with what we will add later, making the design less flexible.
# That is also why, not a single prompt is embedded in any of the classes.
# This module must be no more than an open data structure with some utility methods.
# Extensibility is my primary goal here.

# Maybe all this should be more properly documented somewhere else, but I wont be implementing a group of classes that have:
#     inheritance, flexible default values, partial thread-safeness, open design for async methods, etc every weekend.
# For now, I will keep it as-is here.

class LangTreeElement:
    def __init__(
            self,

            guid=None,
            creation_utc=None):

        # Required, not nullable, auto-initialized:
        self.guid = guid if guid is not None else uuid.uuid4()
        self.creation_utc = creation_utc if creation_utc is not None else pdatetime.get_utc_now()

        # Required, nullable:
        self.parent_element_guid = None
        self.parent_element: LangTreeElement = None

        # Required, nullable (but not encouraged), can be empty:
        self.attributes: dict[str, LangTreeAttribute] = {}
        self.translations: dict[typing.Union[popenai.OpenAiLanguage, str], LangTreeTranslation] = {}
        # These should be dictionaries for performance.
        # Dictionary keys and their corresponding values' internal keys must match.

        # Optional:
        self.client: openai.OpenAI = None
        self.chat_settings: popenai.OpenAiChatSettings = None
        self.timeout = None

    def serialize_to_dict(self):
        dictionary = {}

        # Not nullable:
        dictionary["guid"] = str(self.guid)
        dictionary["creation_utc"] = pdatetime.utc_to_roundtrip_string(self.creation_utc)

        # Nullable:

        if self.parent_element_guid:
            dictionary["parent_element_guid"] = str(self.parent_element_guid)
            # The root element wont have this key present.

        # "parent_element" is not serialized to prevent circular references.

        # Only the dictionary values are serialized.
        # Each value, as a class instance, contains its key.

        if self.attributes:
            dictionary["attributes"] = [attribute.serialize_to_dict() for attribute in sorted(self.attributes.values(), key=lambda attribute: attribute.name)]

        if self.translations:
            dictionary["translations"] = [translation.serialize_to_dict() for translation in sorted(self.translations.values(), key=lambda translation: translation.language_str)]

        # "client", "chat_settings" and "timeout" are not serialized for 2 reasons:
        #     1. These may be inherited from parents to children, making the serialized string representation enormous.
        #     2. If these are set, that would happen to the root element,
        #            making it more logical to consider them as global settings, which must be saved somewhere else.

        return dictionary

class LangTreeMessage(LangTreeElement):
    def __init__(
            self,

            # "user_name" is optional.
            user_role: popenai.OpenAiRole,
            content,

            guid=None,
            creation_utc=None):

        super().__init__(
            guid=guid,
            creation_utc=creation_utc)

        # Optional, but it would be more intuitive to see this in this order in string representations:
        self.user_name = None

        # Required, not nullable:
        self.user_role: popenai.OpenAiRole = user_role
        self.content = content

        # Required, nullable (but not encouraged), can be empty:
        self.child_messages: list[LangTreeMessage] = []
        # The items are loosely expected to be ordered by "creation_utc".

    def serialize_to_dict(self):
        dictionary = {}

        dictionary.update(super().serialize_to_dict())

        # Nullable:

        if self.user_name:
            dictionary["user_name"] = self.user_name
            # If the value is None, the key wont be present.
            # In a single user scenario, this might always be None.

        # Required, not nullable:
        dictionary["user_role"] = self.user_role.value
        dictionary["content"] = self.content

        # Nullable:

        if self.child_messages:
            dictionary["child_messages"] = [child_message.serialize_to_dict() for child_message in sorted(self.child_messages, key=lambda child_message: child_message.creation_utc)]

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

        # Required, not nullable:
        self.name = name
        # Required, nullable:
        self.value = value

    def serialize_to_dict(self):
        dictionary = {}

        dictionary.update(super().serialize_to_dict())

        # Not nullable:
        dictionary["name"] = self.name
        # Nullable:
        dictionary["value"] = self.value
        # Can be none, but the key should be present.

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

        # Required, not nullable:
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

        # Not nullable:
        dictionary["language"] = self.language_str
        dictionary["content"] = self.content

        return dictionary
