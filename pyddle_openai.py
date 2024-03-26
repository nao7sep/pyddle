# Created:
#

import enum
import openai
import pyddle_json_based_kvs as kvs
import tiktoken

# ------------------------------------------------------------------------------
#     Falsy to None
# ------------------------------------------------------------------------------

# https://github.com/openai/openai-python/blob/main/src/openai/_types.py

# OpenAI's official module uses the "NotGiven" class internally for arguments' default values.
# I've tried importing and using it as default values to call the API's methods and encountered errors.
# For now, I'll just send None and see what happens.

def falsy_to_none(value):
    if not value:
        return None

    return value

def falsy_enum_to_none(value):
    if not value:
        return None

    return value.value

# ------------------------------------------------------------------------------
#     Settings
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/api-reference
# https://platform.openai.com/docs/guides/production-best-practices

class OpenAiSettings:
    def __init__(self, kvs_data=None, kvs_key_prefix=None):
        self.kvs_data = kvs_data
        self.kvs_key_prefix = kvs_key_prefix

        self.__api_key = None
        self.__organization = None
        self.__base_url = None

    def get_value(self, key):
        if self.kvs_data:
            return self.kvs_data.get(f"{self.kvs_key_prefix}{key}")

        # We can add data sources here.

        return None

    @property
    def api_key(self):
        if self.__api_key is None:
            self.__api_key = self.get_value("api_key")

        return self.__api_key

    @property
    def organization(self):
        if self.__organization is None:
            self.__organization = self.get_value("organization")

        return self.__organization

    @property
    def base_url(self):
        if self.__base_url is None:
            self.__base_url = self.get_value("base_url")

        return self.__base_url

openai_settings = OpenAiSettings(
    kvs_data=kvs.merged_kvs_data,
    kvs_key_prefix="pyddle_openai/")

# ------------------------------------------------------------------------------
#     Models
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/models

class OpenAiModel(enum.Enum):
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

class OpenAiTokenCounter:
    def __init__(self, model: OpenAiModel):
        self.model: OpenAiModel = model
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
        ''' Returns a list of tokens as decoded strings. OFTEN fails to decode CJK strings. '''

        # If we specify "ignore" or "replace" as the "errors" argument, we can avoid the UnicodeDecodeError,
        #     but the fundamental problem is that the string representation as UTF-8-decoded byte arrays are then cut into tokens with no consideration of the character boundaries,
        #     and therefore there's not much point in just making the method work when half the CJK characters anyway disappear.
        return [self.encoding.decode_single_token_bytes(token).decode("utf-8") for token in self.encode(str)]

gpt_3_5_turbo_token_counter = OpenAiTokenCounter(model=OpenAiModel.GPT_3_5_TURBO)
gpt_4_token_counter = OpenAiTokenCounter(model=OpenAiModel.GPT_4)
gpt_4_turbo_token_counter = OpenAiTokenCounter(model=OpenAiModel.GPT_4_TURBO)
gpt_4_vision_token_counter = OpenAiTokenCounter(model=OpenAiModel.GPT_4_VISION) # May be unnecessary.

# ------------------------------------------------------------------------------
#     Clients
# ------------------------------------------------------------------------------

# https://github.com/openai/openai-python/blob/main/src/openai/_client.py

def create_openai_client(api_key=None, organization=None, base_url=None):
    ''' If the arguments are falsy and cant be retrieved from "openai_settings", environment variables (where the keys are "OPENAI_API_KEY", "OPENAI_ORG_ID" and "OPENAI_BASE_URL") are used internally. '''

    if not api_key:
        api_key = openai_settings.api_key

    if not organization:
        organization = openai_settings.organization

    if not base_url:
        base_url = openai_settings.base_url

    return openai.OpenAI(
        api_key=falsy_to_none(api_key),
        organization=falsy_to_none(organization),
        base_url=falsy_to_none(base_url))

openai_client = create_openai_client()

# ------------------------------------------------------------------------------
#     Text to speech
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/guides/text-to-speech
# https://platform.openai.com/docs/api-reference/audio/createSpeech
# https://github.com/openai/openai-python/blob/main/examples/audio.py
# https://github.com/openai/openai-python/blob/main/src/openai/resources/audio/speech.py

class OpenAiVoice(enum.Enum):
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    NOVA = "nova"
    ONYX = "onyx"
    SHIMMER = "shimmer"

class OpenAiAudioFormat(enum.Enum):
    AAC = "aac"
    FLAC = "flac"
    MP3 = "mp3"
    OPUS = "opus"
    PCM = "pcm"
    WAV = "wav"

# All I want is a one-liner that does just one thing: write the response content to a file with OR without streaming.

# Without "with_streaming_response", "create" returns HttpxBinaryResponseContent, whose "stream_to_file" is deprecated with a message:
#     Due to a bug, this method doesn't actually stream the response content, `.with_streaming_response.method()` should be used instead
# And the code is in: https://github.com/openai/openai-python/blob/main/src/openai/_legacy_response.py

# With "with_streaming_response", "create" returns StreamedBinaryAPIResponse, which seems newer.
# https://github.com/openai/openai-python/blob/main/src/openai/_response.py

# With "with_streaming_response", "stream_to_file" is still a synchronous method.
# I initially assumed it would be an asynchronous method that returns something like C#'s Task.
# The method only "streams" the content, meaning it's appended to the file little by little rather than all at once.

def openai_audio_speech_create_and_stream_to_file(
    model: OpenAiModel,
    voice: OpenAiVoice,
    input,
    response_format: OpenAiAudioFormat, # Defaults to "mp3" in the API, but the user should specify one.
    # Based on the audio format, the user also has to choose the right file extension.
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

class OpenAiTranscriptFormat(enum.Enum):
    JSON = "json"
    SRT = "srt"
    TEXT = "text"
    VERBOSE_JSON = "verbose_json"
    VTT = "vtt"

def openai_audio_transcriptions_create(
    model: OpenAiModel,
    file_path,
    response_format: OpenAiTranscriptFormat,
    language=None,
    prompt=None,
    temperature=None,
    timestamp_granularities=None):

    with open(file_path, "rb") as file:
        return openai_client.audio.transcriptions.create(
            model=model.value,
            file=file,
            response_format=falsy_enum_to_none(response_format),
            language=falsy_to_none(language),
            prompt=falsy_to_none(prompt),
            temperature=falsy_to_none(temperature),
            timestamp_granularities=falsy_to_none(timestamp_granularities))

def openai_audio_translations_create(
    model: OpenAiModel,
    file_path,
    response_format: OpenAiTranscriptFormat,
    prompt=None,
    temperature=None):

    with open(file_path, "rb") as file:
        return openai_client.audio.translations.create(
            model=model.value,
            file=file,
            response_format=falsy_enum_to_none(response_format),
            prompt=falsy_to_none(prompt),
            temperature=falsy_to_none(temperature))
