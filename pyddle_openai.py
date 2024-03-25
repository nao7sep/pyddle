# Created:
#

import openai
import os
import pyddle_json_based_kvs as kvs

# https://platform.openai.com/docs/guides/production-best-practices

# ------------------------------------------------------------------------------
#     Settings
# ------------------------------------------------------------------------------

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
