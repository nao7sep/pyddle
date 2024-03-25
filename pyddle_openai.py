# Created:
#

import enum
import openai
import os
import pyddle_json_based_kvs as kvs
import tiktoken

# ------------------------------------------------------------------------------
#     Settings
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/api-reference
# https://platform.openai.com/docs/guides/production-best-practices

class OpenAiSettings:
    def __init__(self, data_source):
        self.data_source = data_source
        self.__api_key = None
        self.__organization_id = None
        self.__audio_speech_endpoint = None
        self.__audio_transcriptions_endpoint = None
        self.__audio_translations_endpoint = None
        self.__chat_completions_endpoint = None
        self.__images_generations_endpoint = None
        self.__images_edits_endpoint = None
        self.__images_variations_endpoint = None

    def get_value(self, key):
        ''' Attempts to get the value from the environment variables before the data source. '''
        # Returns None if the key is not found.
        value = os.environ.get(key)

        if value:
            return value

        if isinstance(self.data_source, dict):
            return self.data_source.get(key)

        else:
            raise RuntimeError("Unsupported data source type.")

    @property
    def api_key(self):
        if self.__api_key is None:
            self.__api_key = self.get_value("pyddle_openai/api_key")

        return self.__api_key

    @property
    def organization_id(self):
        if self.__organization_id is None:
            self.__organization_id = self.get_value("pyddle_openai/organization_id")

        return self.__organization_id

    @property
    def audio_speech_endpoint(self):
        if self.__audio_speech_endpoint is None:
            self.__audio_speech_endpoint = self.get_value("pyddle_openai/audio_speech_endpoint")

        return self.__audio_speech_endpoint

    @property
    def audio_transcriptions_endpoint(self):
        if self.__audio_transcriptions_endpoint is None:
            self.__audio_transcriptions_endpoint = self.get_value("pyddle_openai/audio_transcriptions_endpoint")

        return self.__audio_transcriptions_endpoint

    @property
    def audio_translations_endpoint(self):
        if self.__audio_translations_endpoint is None:
            self.__audio_translations_endpoint = self.get_value("pyddle_openai/audio_translations_endpoint")

        return self.__audio_translations_endpoint

    @property
    def chat_completions_endpoint(self):
        if self.__chat_completions_endpoint is None:
            self.__chat_completions_endpoint = self.get_value("pyddle_openai/chat_completions_endpoint")

        return self.__chat_completions_endpoint

    @property
    def images_generations_endpoint(self):
        if self.__images_generations_endpoint is None:
            self.__images_generations_endpoint = self.get_value("pyddle_openai/images_generations_endpoint")

        return self.__images_generations_endpoint

    @property
    def images_edits_endpoint(self):
        if self.__images_edits_endpoint is None:
            self.__images_edits_endpoint = self.get_value("pyddle_openai/images_edits_endpoint")

        return self.__images_edits_endpoint

    @property
    def images_variations_endpoint(self):
        if self.__images_variations_endpoint is None:
            self.__images_variations_endpoint = self.get_value("pyddle_openai/images_variations_endpoint")

        return self.__images_variations_endpoint

openai_settings = OpenAiSettings(data_source=kvs.merged_kvs_data)

# ------------------------------------------------------------------------------
#     Models
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/models

class OpenAiModels(enum.Enum):
    TTS_1 = "tts-1"
    TTS_1_HD = "tts-1-hd"
    WHISPER_1 = "whisper-1"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4_VISION = "gpt-4-vision-preview"
    DALL_E_2 = "dall-e-2"
    DALL_E_3 = "dall-e-3"

# ------------------------------------------------------------------------------
#     tiktoken
# ------------------------------------------------------------------------------

# https://github.com/openai/tiktoken
# https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

# In production code, we always need to count tokens to ensure we dont exceed the limit.
# It shouldnt hurt to have to have tiktoken installed in all production environments.

class OpenAiTokenCounter:
    def __init__(self, model: OpenAiModels):
        self.model = model
        self.__encoding = None

    @property
    def encoding(self):
        if self.__encoding is None:
            self.__encoding = tiktoken.encoding_for_model(self.model.value)

        return self.__encoding

    def encode(self, str):
        ''' Returns a list of tokens as integers. '''
        return self.encoding.encode(str)

    def encode_to_strs(self, str):
        ''' Returns a list of tokens as strings. '''
        return [self.encoding.decode_single_token_bytes(token).decode("utf-8") for token in self.encode(str)]

# I'm not sure if we need an instance for Vision.
# tiktoken.encoding_for_model doesnt raise an error and returns cl100k_base for Vision.
# The instance anyway initializes itself only when it's used.

gpt_3_5_turbo_token_counter = OpenAiTokenCounter(model=OpenAiModels.GPT_3_5_TURBO)
gpt_4_token_counter = OpenAiTokenCounter(model=OpenAiModels.GPT_4)
gpt_4_turbo_token_counter = OpenAiTokenCounter(model=OpenAiModels.GPT_4_TURBO)
gpt_4_vision_token_counter = OpenAiTokenCounter(model=OpenAiModels.GPT_4_VISION)
