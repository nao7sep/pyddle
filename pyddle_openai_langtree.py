﻿# Created:
# A module that helps us organize knowledge in a tree structure.

import typing
import uuid

import openai

import pyddle_datetime as pdatetime
import pyddle_openai as popenai
import pyddle_type as ptype

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

    def get_root_element(self):
        element = self

        while element.parent_element:
            element = element.parent_element

        return element

    def create_attribute(self, name, value):
        attribute = LangTreeAttribute(
            name=name,
            value=value
        )

        attribute.parent_element_guid = self.guid
        attribute.parent_element = self

        attribute.client = self.client
        attribute.chat_settings = self.chat_settings
        attribute.timeout = self.timeout

        self.attributes[attribute.name] = attribute

        return attribute

    def create_translation(self, language: typing.Union[popenai.OpenAiLanguage, str], content):
        translation = LangTreeTranslation(
            language=language,
            content=content
        )

        translation.parent_element_guid = self.guid
        translation.parent_element = self

        translation.client = self.client
        translation.chat_settings = self.chat_settings
        translation.timeout = self.timeout

        self.translations[translation.language] = translation

        return translation

    # Moves "attributes" and "translations" to the end of the dictionary.
    # Since Python 3.7, dictionaries are ordered by insertion order.

    @staticmethod
    def _update_key_order(dictionary):
        if "attributes" in dictionary:
            attributes = dictionary["attributes"]
            del dictionary["attributes"]
            dictionary["attributes"] = attributes

        if "translations" in dictionary:
            translations = dictionary["translations"]
            del dictionary["translations"]
            dictionary["translations"] = translations

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

    @staticmethod
    def _deserialize_common_fields(element, dictionary):
        if "parent_element_guid" in dictionary:
            element.parent_element_guid = uuid.UUID(dictionary["parent_element_guid"])

        if "attributes" in dictionary:
            for attribute_dict in dictionary["attributes"]:
                attribute = LangTreeAttribute.deserialize_from_dict(attribute_dict)

                # attribute.parent_element_guid = element.guid
                attribute.parent_element = element

                element.attributes[attribute.name] = attribute

        if "translations" in dictionary:
            for translation_dict in dictionary["translations"]:
                translation = LangTreeTranslation.deserialize_from_dict(translation_dict)

                # translation.parent_element_guid = element.guid
                translation.parent_element = element

                element.translations[translation.language] = translation

        return element

    @staticmethod
    def deserialize_from_dict(dictionary):
        element = LangTreeElement(
            guid=uuid.UUID(dictionary["guid"]),
            creation_utc=pdatetime.roundtrip_string_to_utc(dictionary["creation_utc"])
        )

        LangTreeElement._deserialize_common_fields(element, dictionary)

        return element

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

    def create_child_message(self, user_role: popenai.OpenAiRole, content, user_name=None):
        child_message = LangTreeMessage(
            user_role=user_role,
            content=content
        )

        child_message.user_name = user_name

        child_message.parent_element_guid = self.guid
        child_message.parent_element = self

        child_message.client = self.client
        child_message.chat_settings = self.chat_settings
        child_message.timeout = self.timeout

        self.child_messages.append(child_message)

        return child_message

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

        LangTreeElement._update_key_order(dictionary)

        return dictionary

    @staticmethod
    def deserialize_from_dict(dictionary):
        message = LangTreeMessage(
            user_role=popenai.OpenAiRole(dictionary["user_role"]),
            content=dictionary["content"],

            guid=uuid.UUID(dictionary["guid"]),
            creation_utc=pdatetime.roundtrip_string_to_utc(dictionary["creation_utc"])
        )

        LangTreeElement._deserialize_common_fields(message, dictionary)

        if "user_name" in dictionary:
            message.user_name = dictionary["user_name"]

        if "child_messages" in dictionary:
            for child_message_dict in dictionary["child_messages"]:
                child_message = LangTreeMessage.deserialize_from_dict(child_message_dict)

                # child_message.parent_element_guid = message.guid
                child_message.parent_element = message

                message.child_messages.append(child_message)

        return message

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

        LangTreeElement._update_key_order(dictionary)

        return dictionary

    @staticmethod
    def deserialize_from_dict(dictionary):
        attribute = LangTreeAttribute(
            name=dictionary["name"],
            value=dictionary["value"],

            guid=uuid.UUID(dictionary["guid"]),
            creation_utc=pdatetime.roundtrip_string_to_utc(dictionary["creation_utc"])
        )

        LangTreeElement._deserialize_common_fields(attribute, dictionary)

        return attribute

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

        LangTreeElement._update_key_order(dictionary)

        return dictionary

    @staticmethod
    def deserialize_from_dict(dictionary):
        language = ptype.str_to_enum_by_str_value(dictionary["language"], popenai.OpenAiLanguage, ignore_case=True)

        if language is None:
            language = dictionary["language"]

        translation = LangTreeTranslation(
            language=language,
            content=dictionary["content"],

            guid=uuid.UUID(dictionary["guid"]),
            creation_utc=pdatetime.roundtrip_string_to_utc(dictionary["creation_utc"])
        )

        LangTreeElement._deserialize_common_fields(translation, dictionary)

        return translation