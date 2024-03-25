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

# OpenAI's official module reads environment variables associated with keys including
#     "OPENAI_API_KEY", "OPENAI_ORG_ID" and "OPENAI_BASE_URL".
# Currently, pyddle_openai wouldnt be much more than a sugar-coated wrapper
#     and situations where it must coexist with code that uses the official module must be expected.
# So, we will read environment variables with different keys and,
#     if they are not found, fallback to a JSON-based KVS data source for now.

class OpenAiSettings:
    def __init__(self, data_source):
        self.data_source = data_source
        self.__api_key = None
        self.__organization = None
        self.__base_url = None

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
    def organization(self):
        if self.__organization is None:
            self.__organization = self.get_value("pyddle_openai/organization")

        return self.__organization

    @property
    def base_url(self):
        if self.__base_url is None:
            self.__base_url = self.get_value("pyddle_openai/base_url")

        return self.__base_url

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

# In production code, we would always need to count tokens to ensure we dont exceed the limit.
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

# ------------------------------------------------------------------------------
#     Clients
# ------------------------------------------------------------------------------

# https://github.com/openai/openai-python/blob/main/src/openai/_client.py

# If the arguments are not provided, the function will attempt to read them from environment variables
#     using keys different from those the official module uses for reasons explained above
#     and then falls back to the JSON-based KVS data source.
# If they are still falsy, the OpenAI class's constructor will try reading
#     "OPENAI_API_KEY", "OPENAI_ORG_ID" and "OPENAI_BASE_URL".

def create_openai_client(api_key=None, organization=None, base_url=None):
    if not api_key:
        api_key = openai_settings.api_key

    if not organization:
        organization = openai_settings.organization

    if not base_url:
        base_url = openai_settings.base_url

    return openai.OpenAI(api_key=api_key, organization=organization, base_url=base_url)

openai_client = create_openai_client()

# ------------------------------------------------------------------------------
#     Text to speech
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/guides/text-to-speech
# https://platform.openai.com/docs/api-reference/audio/createSpeech
# https://github.com/openai/openai-python/blob/main/examples/audio.py
# https://github.com/openai/openai-python/blob/main/src/openai/resources/audio/speech.py

class OpenAiVoices(enum.Enum):
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    NOVA = "nova"
    ONYX = "onyx"
    SHIMMER = "shimmer"

class OpenAiAudioFormats(enum.Enum):
    AAC = "aac"
    FLAC = "flac"
    MP3 = "mp3"
    OPUS = "opus"
    PCM = "pcm"
    WAV = "wav"

# Without "with_streaming_response", "create" returns HttpxBinaryResponseContent.
# Its "stream_to_file" is deprecated with the following message:
#     Due to a bug, this method doesn't actually stream the response content, `.with_streaming_response.method()` should be used instead
# https://github.com/openai/openai-python/blob/main/src/openai/_legacy_response.py

# With "with_streaming_response", "create" returns StreamedBinaryAPIResponse.
# I havent done much research on this, but the code looks a lot newer.
# https://github.com/openai/openai-python/blob/main/src/openai/_response.py

# I dont expect this one-liner to really stream the response content.
# Most probably, I will anyway use it in a synchronous manner and wait for the method to finish.
# There are better ways to stream audio, one of which is introduced on the page linked above.

# The default value for "response_format" in the API is "mp3".
# As the format affects the file extension, I dont think it needs to default to anything.

def openai_audio_speech_stream_to_file(
    model: OpenAiModels,
    voice: OpenAiVoices,
    input,
    response_format: OpenAiAudioFormats,
    file_path):

    with openai_client.audio.speech.with_streaming_response.create(
        model=model.value,
        voice=voice.value,
        input=input,
        response_format=response_format.value) as response:

        response.stream_to_file(file_path)

# ------------------------------------------------------------------------------
#     Speech to text
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/guides/speech-to-text
# https://platform.openai.com/docs/api-reference/audio/createTranscription
# https://platform.openai.com/docs/api-reference/audio/createTranslation
# https://github.com/openai/openai-python/blob/main/src/openai/resources/audio/transcriptions.py
# https://github.com/openai/openai-python/blob/main/src/openai/resources/audio/translations.py

class OpenAiTranscriptFormats(enum.Enum):
    JSON = "json"
    SRT = "srt"
    TEXT = "text"
    VERBOSE_JSON = "verbose_json"
    VTT = "vtt"

# Unlike openai_audio_speech_stream_to_file, there's nothing to do after "create".
def openai_audio_transcriptions_create(
    model: OpenAiModels,
    file_path,
    language=None,
    prompt=None,
    response_format: OpenAiTranscriptFormats = None,
    temperature=None,
    timestamp_granularities=None):

    if response_format:
        response_format_str = response_format.value

    else:
        response_format_str = None

    with open(file_path, "rb") as file:
        return openai_client.audio.transcriptions.create(
            model=model.value,
            file=file,
            language=language,
            prompt=prompt,
            response_format=response_format_str,
            temperature=temperature,
            timestamp_granularities=timestamp_granularities)

def openai_audio_translations_create(
    model: OpenAiModels,
    file_path,
    prompt=None,
    response_format: OpenAiTranscriptFormats = None,
    temperature=None):

    if response_format:
        response_format_str = response_format.value

    else:
        response_format_str = None

    with open(file_path, "rb") as file:
        return openai_client.audio.translations.create(
            model=model.value,
            file=file,
            prompt=prompt,
            response_format=response_format_str,
            temperature=temperature)
