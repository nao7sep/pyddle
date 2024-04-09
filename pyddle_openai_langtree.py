# Created: 2024-04-08
# A module that helps us organize knowledge in a tree structure.

from __future__ import annotations
import typing
import uuid

import openai

import pyddle_datetime as pdatetime
import pyddle_openai as popenai
import pyddle_type as ptype
import pyddle_utility as putility

# The comments regarding this module werent particularly "episodic",
#     but they were moved to BX24 in SH77 langtree-related Comments.json.

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

    def _get_client(self, client: openai.OpenAI):
        return putility.get_not_none_or_call_func(
            popenai.get_openai_default_client,
            client,
            self.client)

    def _get_chat_settings(self, chat_settings: popenai.OpenAiChatSettings):
        return putility.get_not_none_or_call_func(
            popenai.get_openai_default_chat_settings,
            chat_settings,
            self.chat_settings)

    def _get_response_timeout(self, timeout):
        return putility.get_not_none(
            timeout,
            self.timeout,
            popenai.DEFAULT_RESPONSE_TIMEOUT)

    def generate_attribute_with_prompt(
        self,

        name,
        prompt,

        client: openai.OpenAI=None,
        chat_settings: popenai.OpenAiChatSettings=None,
        timeout=None):

        response = popenai.openai_chat_completions_create_with_settings(
            settings=self._get_chat_settings(chat_settings),
            messages=popenai.openai_build_messages(prompt),
            client=self._get_client(client),
            timeout=self._get_response_timeout(timeout)
        )

        value = popenai.openai_extract_first_message(response)

        return self.create_attribute(name, value)

    def generate_translation_with_prompt(
        self,

        language: typing.Union[popenai.OpenAiLanguage, str],
        prompt,

        client: openai.OpenAI=None,
        chat_settings: popenai.OpenAiChatSettings=None,
        timeout=None):

        response = popenai.openai_chat_completions_create_with_settings(
            settings=self._get_chat_settings(chat_settings),
            messages=popenai.openai_build_messages(prompt),
            client=self._get_client(client),
            timeout=self._get_response_timeout(timeout)
        )

        content = popenai.openai_extract_first_message(response)

        return self.create_translation(language, content)

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

    def generate_child_message_with_messages(
        self,

        messages,

        client: openai.OpenAI=None,
        chat_settings: popenai.OpenAiChatSettings=None,
        timeout=None):

        response = popenai.openai_chat_completions_create_with_settings(
            settings=self._get_chat_settings(chat_settings),
            messages=messages,
            client=self._get_client(client),
            timeout=self._get_response_timeout(timeout)
        )

        content = popenai.openai_extract_first_message(response)

        return self.create_child_message(
            user_role=popenai.OpenAiRole.SYSTEM,
            content=content)

    def generate_child_message_with_context_builder(
        self,

        context_builder: LangTreeContextBuilder,

        client: openai.OpenAI=None,
        chat_settings: popenai.OpenAiChatSettings=None,
        timeout=None):

        return self.generate_child_message_with_messages(
            context_builder.build_messages(self),

            client=client,
            chat_settings=chat_settings,
            timeout=timeout)

    def generate_child_message(
        self,

        client: openai.OpenAI=None,
        chat_settings: popenai.OpenAiChatSettings=None,
        timeout=None):

        return self.generate_child_message_with_context_builder(
            context_builder=get_langtree_default_context_builder(),

            client=client,
            chat_settings=chat_settings,
            timeout=timeout)

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

# Episodic comments available: GL84 in SH77 langtree-related Comments.json

class LangTreeContextBuilder:
    def __init__(
        self,

        # Refer to the episodic comments regarding the default values.

        max_number_of_system_messages=None,
        max_number_of_system_message_summaries=0,

        max_number_of_user_messages=2,
        max_number_of_user_message_summaries=2,

        max_number_of_assistant_messages=1,
        max_number_of_assistant_message_summaries=2):

        self.max_number_of_system_messages = max_number_of_system_messages
        self.max_number_of_system_message_summaries = max_number_of_system_message_summaries

        self.max_number_of_user_messages = max_number_of_user_messages
        self.max_number_of_user_message_summaries = max_number_of_user_message_summaries

        self.max_number_of_assistant_messages = max_number_of_assistant_messages
        self.max_number_of_assistant_message_summaries = max_number_of_assistant_message_summaries

    def build_messages(self, message: LangTreeMessage):
        elements_with_contents = []

        # With C#'s "ref" or maintaining a list of max numbers, the following code could be shorter.

        number_of_system_messages = 0
        number_of_system_message_summaries = 0
        number_of_user_messages = 0
        number_of_user_message_summaries = 0
        number_of_assistant_messages = 0
        number_of_assistant_message_summaries = 0

        element = message

        while True:
            if element.user_role == popenai.OpenAiRole.SYSTEM:
                if self.max_number_of_system_messages is None or number_of_system_messages < self.max_number_of_system_messages:
                    elements_with_contents.append((element, element.content)) # Tuple of (element, full content)
                    number_of_system_messages += 1

                elif self.max_number_of_system_message_summaries is None or number_of_system_message_summaries < self.max_number_of_system_message_summaries:
                    elements_with_contents.append((element, element.attributes["summary"].value)) # If the summary is not available, this should raise an exception.
                    number_of_system_message_summaries += 1

            elif element.user_role == popenai.OpenAiRole.USER:
                if self.max_number_of_user_messages is None or number_of_user_messages < self.max_number_of_user_messages:
                    elements_with_contents.append((element, element.content))
                    number_of_user_messages += 1

                elif self.max_number_of_user_message_summaries is None or number_of_user_message_summaries < self.max_number_of_user_message_summaries:
                    elements_with_contents.append((element, element.attributes["summary"].value))
                    number_of_user_message_summaries += 1

            elif element.user_role == popenai.OpenAiRole.ASSISTANT:
                if self.max_number_of_assistant_messages is None or number_of_assistant_messages < self.max_number_of_assistant_messages:
                    elements_with_contents.append((element, element.content))
                    number_of_assistant_messages += 1

                elif self.max_number_of_assistant_message_summaries is None or number_of_assistant_message_summaries < self.max_number_of_assistant_message_summaries:
                    elements_with_contents.append((element, element.attributes["summary"].value))
                    number_of_assistant_message_summaries += 1

            else:
                raise RuntimeError(f"Unknown user role: {element.user_role}")

            if element.parent_element:
                element = element.parent_element

            else:
                break

        messages = []

        for element, content in sorted(elements_with_contents, key=lambda element_with_content: element_with_content[0].creation_utc):
            messages.append(popenai.openai_build_message(element.user_role, content, name=element.user_name)) # Supports multi-user scenarios.

        return messages

# Lazy loading:
__langtree_default_context_builder = None # pylint: disable=invalid-name

def get_langtree_default_context_builder():
    global __langtree_default_context_builder # pylint: disable=global-statement

    if __langtree_default_context_builder is None:
        __langtree_default_context_builder = LangTreeContextBuilder()

    return __langtree_default_context_builder
