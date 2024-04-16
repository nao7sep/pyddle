# Created: 2024-04-10
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

# Now langtree is "technically" free from the pyddle_openai module,
#     meaning, by adding type annotations and code that utilizes isinstance,
#     langtree should be able to work with other AI APIs.

class Element:
    def __init__(
        self,

        guid = None,
        creation_utc = None):

        # Required, not nullable, auto-initialized:
        self.guid = guid if guid is not None else uuid.uuid4()
        self.creation_utc = creation_utc if creation_utc is not None else pdatetime.get_utc_now()

        # Required, nullable:
        self.parent_element_guid = None
        self.parent_element: Element | None = None

        # Required, nullable (but not encouraged), can be empty:
        self.attributes: dict[str, Attribute] = {}
        self.translations: dict[popenai.Language | str, Translation] = {}
        # These should be dictionaries for performance.
        # Dictionary keys and their corresponding values' internal keys must match.

        # Optional:
        self.client: openai.OpenAI | None = None
        self.chat_settings: popenai.ChatSettings | None = None
        self.timeout = None

    def get_root_element(self):
        element = self

        while element.parent_element:
            element = element.parent_element

        return element

    def create_attribute(self, name, value):
        attribute = Attribute(
            name = name,
            value = value)

        attribute.parent_element_guid = self.guid
        attribute.parent_element = self

        attribute.client = self.client
        attribute.chat_settings = self.chat_settings
        attribute.timeout = self.timeout

        self.attributes[attribute.name] = attribute

        return attribute

    def create_translation(self, language: popenai.Language | str, content):
        translation = Translation(
            language = language,
            content = content)

        translation.parent_element_guid = self.guid
        translation.parent_element = self

        translation.client = self.client
        translation.chat_settings = self.chat_settings
        translation.timeout = self.timeout

        self.translations[translation.language] = translation

        return translation

    def _get_client(self, client: openai.OpenAI | None):
        return putility.get_not_none_or_call_func(
            popenai.get_default_client,
            client,
            self.client)

    def _get_chat_settings(self, chat_settings: popenai.ChatSettings | None):
        return putility.get_not_none_or_call_func(
            popenai.get_default_chat_settings,
            chat_settings,
            self.chat_settings)

    def _get_response_timeout(self, timeout):
        return putility.get_not_none(
            timeout,
            self.timeout,
            popenai.DEFAULT_RESPONSE_TIMEOUT)

    def _get_chunk_timeout(self, timeout):
        return putility.get_not_none(
            timeout,
            self.timeout,
            popenai.DEFAULT_CHUNK_TIMEOUT)

    def generate_attribute_with_prompt(
        self,

        name,
        prompt,

        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        response = popenai.create_chat_completions_with_settings(
            settings = self._get_chat_settings(chat_settings),
            messages = popenai.build_messages(prompt),
            client = self._get_client(client),
            timeout = self._get_response_timeout(timeout))

        value = popenai.extract_first_message(response)

        return self.create_attribute(name, value)

    def generate_translation_with_prompt(
        self,

        language: popenai.Language | str,
        prompt,

        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        response = popenai.create_chat_completions_with_settings(
            settings = self._get_chat_settings(chat_settings),
            messages = popenai.build_messages(prompt),
            client = self._get_client(client),
            timeout = self._get_response_timeout(timeout))

        content = popenai.extract_first_message(response)

        return self.create_translation(language, content)

    # Moves "attributes", "translations" and "child_messages" to the end of the dictionary for better readability.
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

        if "child_messages" in dictionary:
            child_messages = dictionary["child_messages"]
            del dictionary["child_messages"]
            dictionary["child_messages"] = child_messages

    def serialize_to_dict(self):
        # Values will be strings and dictionaries.
        dictionary: dict[str, typing.Any] = {}

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
            dictionary["attributes"] = [attribute.serialize_to_dict() for attribute in sorted(self.attributes.values(), key = lambda attribute: attribute.name)]

        if self.translations:
            dictionary["translations"] = [translation.serialize_to_dict() for translation in sorted(self.translations.values(), key = lambda translation: translation.language_str)]

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
                attribute = Attribute.deserialize_from_dict(attribute_dict)

                # attribute.parent_element_guid = element.guid
                attribute.parent_element = element

                element.attributes[attribute.name] = attribute

        if "translations" in dictionary:
            for translation_dict in dictionary["translations"]:
                translation = Translation.deserialize_from_dict(translation_dict)

                # translation.parent_element_guid = element.guid
                translation.parent_element = element

                element.translations[translation.language] = translation

        return element

    @staticmethod
    def deserialize_from_dict(dictionary):
        element = Element(
            guid = uuid.UUID(dictionary["guid"]),
            creation_utc = pdatetime.roundtrip_string_to_utc(dictionary["creation_utc"]))

        Element._deserialize_common_fields(element, dictionary)

        return element

class Message(Element):
    def __init__(
        self,

        # "user_name" is optional.
        user_role: popenai.Role,
        content,

        guid = None,
        creation_utc = None):

        super().__init__(
            guid = guid,
            creation_utc = creation_utc)

        # Optional, but it would be more intuitive to see this in this order in string representations:
        self.user_name = None

        # Required, not nullable:
        self.user_role: popenai.Role = user_role
        self.content = content

        # Optional, nullable, not serialized:
        # Comments: SH77 langtree-related Comments.json
        self.token_count: int | None = None

        # Required, nullable (but not encouraged), can be empty:
        self.child_messages: list[Message] = []
        # The items are loosely expected to be ordered by "creation_utc".

    def create_child_message(
        self,
        user_role: popenai.Role,
        content,
        user_name = None):

        ''' Consider using "create_sibling_message" instead. '''

        child_message = Message(
            user_role = user_role,
            content = content)

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
        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        ''' Consider using "generate_sibling_message_with_messages" instead. '''

        response = popenai.create_chat_completions_with_settings(
            settings = self._get_chat_settings(chat_settings),
            messages = messages,
            client = self._get_client(client),
            timeout = self._get_response_timeout(timeout))

        content = popenai.extract_first_message(response)

        return self.create_child_message(
            user_role = popenai.Role.ASSISTANT,
            content = content)

    def generate_child_message_with_context_builder(
        self,
        context_builder: ContextBuilder,
        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        ''' Consider using "generate_sibling_message_with_context_builder" instead. '''

        return self.generate_child_message_with_messages(
            context_builder.build(self),

            client = client,
            chat_settings = chat_settings,
            timeout = timeout)

    def generate_child_message(
        self,
        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        ''' Consider using "generate_sibling_message" instead. '''

        return self.generate_child_message_with_context_builder(
            context_builder = get_default_context_builder(),

            client = client,
            chat_settings = chat_settings,
            timeout = timeout)

    def create_sibling_message(
        self,
        user_role: popenai.Role,
        content,
        user_name = None):

        ''' Creates the youngest sibling message at the same level regardless of which message "self" points to. '''

        if self.parent_element:
            return typing.cast(Message, self.parent_element).create_child_message(user_role = user_role, content = content, user_name = user_name)

        else:
            return self.create_child_message(user_role = user_role, content = content, user_name = user_name)

    def generate_sibling_message_with_messages(
        self,
        messages,
        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        ''' Generates the youngest sibling message at the same level regardless of which message "self" points to. '''

        if self.parent_element:
            return typing.cast(Message, self.parent_element).generate_child_message_with_messages(messages, client = client, chat_settings = chat_settings, timeout = timeout)

        else:
            return self.generate_child_message_with_messages(messages, client = client, chat_settings = chat_settings, timeout = timeout)

    def generate_sibling_message_with_context_builder(
        self,
        context_builder: ContextBuilder,
        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        ''' Generates the youngest sibling message at the same level regardless of which message "self" points to. '''

        if self.parent_element:
            return typing.cast(Message, self.parent_element).generate_child_message_with_context_builder(context_builder, client = client, chat_settings = chat_settings, timeout = timeout)

        else:
            return self.generate_child_message_with_context_builder(context_builder, client = client, chat_settings = chat_settings, timeout = timeout)

    def generate_sibling_message(
        self,
        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        ''' Generates the youngest sibling message at the same level regardless of which message "self" points to. '''

        if self.parent_element:
            return typing.cast(Message, self.parent_element).generate_child_message(client = client, chat_settings = chat_settings, timeout = timeout)

        else:
            return self.generate_child_message(client = client, chat_settings = chat_settings, timeout = timeout)

    def start_generating_message_with_messages(
        self,
        messages,
        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        return popenai.create_chat_completions_with_settings(
            settings = self._get_chat_settings(chat_settings),
            messages = messages,
            client = self._get_client(client),
            stream_override = True,
            timeout = self._get_chunk_timeout(timeout)) # Timeout for chunks.

    def start_generating_message_with_context_builder(
        self,
        context_builder: ContextBuilder,
        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        return self.start_generating_message_with_messages(
            context_builder.build(self),

            client = client,
            chat_settings = chat_settings,
            timeout = timeout)

    def start_generating_message(
        self,
        client: openai.OpenAI | None = None,
        chat_settings: popenai.ChatSettings | None = None,
        timeout = None):

        return self.start_generating_message_with_context_builder(
            context_builder = get_default_context_builder(),

            client = client,
            chat_settings = chat_settings,
            timeout = timeout)

    def get_previous_message(self):
        ''' Assumes child messages at each level are ordered by "creation_utc". '''

        if self.parent_element:
            parent_element = typing.cast(Message, self.parent_element)

            index = parent_element.child_messages.index(self)

            if index >= 1:
                return parent_element.child_messages[index - 1]

            else:
                return parent_element

        return None

    def get_next_message(self, sibling_first = True):
        ''' Assumes child messages at each level are ordered by "creation_utc". '''

        def _get_sibling():
            if self.parent_element:
                parent_element = typing.cast(Message, self.parent_element)

                index = parent_element.child_messages.index(self)

                if index + 1 < len(parent_element.child_messages):
                    return parent_element.child_messages[index + 1]

            return None

        def _get_child():
            if self.child_messages:
                return self.child_messages[0]

            return None

        if sibling_first:
            return _get_sibling() or _get_child()

        else:
            return _get_child() or _get_sibling()

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
            dictionary["child_messages"] = [child_message.serialize_to_dict() for child_message in sorted(self.child_messages, key = lambda child_message: child_message.creation_utc)]

        Element._update_key_order(dictionary)

        return dictionary

    @staticmethod
    def deserialize_from_dict(dictionary):
        message = Message(
            user_role = popenai.Role(dictionary["user_role"]),
            content = dictionary["content"],

            guid = uuid.UUID(dictionary["guid"]),
            creation_utc = pdatetime.roundtrip_string_to_utc(dictionary["creation_utc"]))

        Element._deserialize_common_fields(message, dictionary)

        if "user_name" in dictionary:
            message.user_name = dictionary["user_name"]

        if "child_messages" in dictionary:
            for child_message_dict in dictionary["child_messages"]:
                child_message = Message.deserialize_from_dict(child_message_dict)

                # child_message.parent_element_guid = message.guid
                child_message.parent_element = message

                message.child_messages.append(child_message)

        return message

class Attribute(Element):
    def __init__(
        self,

        name,
        value,

        guid = None,
        creation_utc = None):

        super().__init__(
            guid = guid,
            creation_utc = creation_utc)

        # Required, not nullable:
        self.name = name
        # Required, nullable:
        self.value = value

        # Optional, nullable, not serialized:
        # Comments: SH77 langtree-related Comments.json
        self.token_count = None

    def serialize_to_dict(self):
        dictionary = {}

        dictionary.update(super().serialize_to_dict())

        # Not nullable:
        dictionary["name"] = self.name
        # Nullable:
        dictionary["value"] = self.value
        # Can be none, but the key should be present.

        Element._update_key_order(dictionary)

        return dictionary

    @staticmethod
    def deserialize_from_dict(dictionary):
        attribute = Attribute(
            name = dictionary["name"],
            value = dictionary["value"],

            guid = uuid.UUID(dictionary["guid"]),
            creation_utc = pdatetime.roundtrip_string_to_utc(dictionary["creation_utc"]))

        Element._deserialize_common_fields(attribute, dictionary)

        return attribute

class Translation(Element):
    def __init__(
        self,

        language: popenai.Language | str,
        content,

        guid = None,
        creation_utc = None):

        super().__init__(
            guid = guid,
            creation_utc = creation_utc)

        # Required, not nullable:
        self.language: popenai.Language | str = language
        self.content = content

        # Optional, nullable, not serialized:
        # Comments: SH77 langtree-related Comments.json
        self.token_count = None

    @property
    def language_str(self):
        if isinstance(self.language, popenai.Language):
            return self.language.value

        return self.language

    def serialize_to_dict(self):
        dictionary = {}

        dictionary.update(super().serialize_to_dict())

        # Not nullable:
        dictionary["language"] = self.language_str
        dictionary["content"] = self.content

        Element._update_key_order(dictionary)

        return dictionary

    @staticmethod
    def deserialize_from_dict(dictionary):
        language = ptype.str_to_enum_by_str_value(dictionary["language"], popenai.Language, ignore_case = True)

        if language is None:
            language = dictionary["language"]

        translation = Translation(
            language = language,
            content = dictionary["content"],

            guid = uuid.UUID(dictionary["guid"]),
            creation_utc = pdatetime.roundtrip_string_to_utc(dictionary["creation_utc"]))

        Element._deserialize_common_fields(translation, dictionary)

        return translation

# Episodic comments available: SH77 langtree-related Comments.json

class ContextBuilder:
    def __init__(
        self,

        # Refer to the episodic comments regarding the default values.

        max_number_of_system_messages = None, # No limit.
        max_total_tokens_of_system_messages = None, # No limit.

        max_number_of_user_messages = 3,
        max_total_tokens_of_user_messages = 4096,

        max_number_of_assistant_messages = 3,
        max_total_tokens_of_assistant_messages = 4096):

        self.max_number_of_system_messages = max_number_of_system_messages
        self.max_total_tokens_of_system_messages = max_total_tokens_of_system_messages

        self.max_number_of_user_messages = max_number_of_user_messages
        self.max_total_tokens_of_user_messages = max_total_tokens_of_user_messages

        self.max_number_of_assistant_messages = max_number_of_assistant_messages
        self.max_total_tokens_of_assistant_messages = max_total_tokens_of_assistant_messages

        # Optional:
        self.token_counter = None

    def _get_token_counter(self, token_counter: popenai.TokenCounter | None):
        return putility.get_not_none_or_call_func(
            popenai.get_default_token_counter,
            token_counter,
            self.token_counter)

    def build(
        self,
        message: Message,
        token_counter: popenai.TokenCounter | None = None) -> Context:

        # All younger siblings and the root element.
        elements = []

        element = message

        while True:
            # In each round, we collect all the siblings of the current element that are younger together with the element itself OR the element alone if it's the root element.

            # Considerations:
            #     * When there are older siblings than the currently selected element, they are properly excluded from the list
            #     * When the selected element is a part of a branch hanging from a somewhere-in-the middle sibling,
            #           the search should properly go up to the root element including only what it should

            if element.parent_element:
                parent_element = typing.cast(Message, element.parent_element)

                for sibling in parent_element.child_messages:
                    if sibling.creation_utc < element.creation_utc:
                        elements.append(sibling)

                elements.append(element) # As an element that has a parent and may have younger siblings.

                element = parent_element

            else:
                elements.append(element) # As the root element.

                break

        # No matter how the tree structure has been built, no child is older than its parent.
        elements.sort(key = lambda element: element.creation_utc, reverse = True)

        # Reducing the "if" statements:

        max_numbers = [self.max_number_of_system_messages, self.max_number_of_user_messages, self.max_number_of_assistant_messages]
        numbers = [0, 0, 0]

        max_total_tokens = [self.max_total_tokens_of_system_messages, self.max_total_tokens_of_user_messages, self.max_total_tokens_of_assistant_messages]
        total_tokens = [0, 0, 0]

        elements_to_include = []

        # We can just update "token_counter", but I like to keep arguments unchanged.
        token_counter_to_use = self._get_token_counter(token_counter)

        for element in elements:
            if element.user_role == popenai.Role.SYSTEM:
                index = 0

            elif element.user_role == popenai.Role.USER:
                index = 1

            elif element.user_role == popenai.Role.ASSISTANT:
                index = 2

            else:
                raise RuntimeError(f"Unknown user role: {element.user_role}")

            if element.token_count is None:
                element.token_count = token_counter_to_use.count(element.content)

            if max_numbers[index] is None or numbers[index] < max_numbers[index]:
                if max_total_tokens[index] is None or total_tokens[index] + element.token_count <= max_total_tokens[index]:
                    elements_to_include.append(element)

                    numbers[index] += 1
                    total_tokens[index] += element.token_count

        elements_to_include.sort(key = lambda element: element.creation_utc)

        messages = [popenai.create_message(role = element.user_role, content = element.content, name = element.user_name) for element in elements_to_include]

        return Context(
            elements = elements_to_include,
            messages = messages)

# Lazy loading:
__default_context_builder: ContextBuilder | None = None # pylint: disable = invalid-name

def get_default_context_builder():
    global __default_context_builder # pylint: disable = global-statement

    if __default_context_builder is None:
        __default_context_builder = ContextBuilder()

    return __default_context_builder

class Context:
    def __init__(
        self,

        elements: list[Message],
        messages: list[dict]):

        self.elements = elements
        self.messages = messages

    def get_elements_by_role(self, role: popenai.Role):
        return [element for element in self.elements if element.user_role == role]

    def get_statistics(self):
        statistics = {}

        def _add(role: popenai.Role):
            elements = self.get_elements_by_role(role)

            statistics[role] = {
                "number": len(elements),
                "total_tokens": sum(element.token_count for element in elements),
                "tokens": [element.token_count for element in elements]
            }

        _add(popenai.Role.SYSTEM)
        _add(popenai.Role.USER)
        _add(popenai.Role.ASSISTANT)

        return statistics

    @staticmethod
    def statistics_to_lines(statistics, all_tokens = False):
        def _get_line(role: popenai.Role):
            number = statistics[role]["number"]
            total_tokens = statistics[role]["total_tokens"]

            if all_tokens and total_tokens > 0:
                tokens = statistics[role]["tokens"]

                return f"{role.value.capitalize()}: {number} messages ({total_tokens} tokens: {", ".join([str(token) for token in tokens])})"

            else:
                return f"{role.value.capitalize()}: {number} messages ({total_tokens} tokens)"

        return [
            _get_line(popenai.Role.SYSTEM),
            _get_line(popenai.Role.USER),
            _get_line(popenai.Role.ASSISTANT)
        ]
