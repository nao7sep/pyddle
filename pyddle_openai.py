# Created:
#

import enum
import openai
import os
import pyddle_collections as collections
import pyddle_json_based_kvs as kvs
import pyddle_file_system as file_system
import pyddle_path # as path
import requests
import tiktoken

# This script contains some one-liners.
# I will keep their names simple and stupid because I might want to add more later.

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

    args = collections.PotentiallyFalsyArgs()
    args.may_contain("api_key", api_key)
    args.may_contain("organization", organization)
    args.may_contain("base_url", base_url)

    return openai.OpenAI(**args.args)

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
    # Output:
    file_path,

    # Input:
    input,

    # Parameters:
    model: OpenAiModel,
    voice: OpenAiVoice,
    response_format: OpenAiAudioFormat, # Defaults to "mp3" in the API, but the user should specify one.
    # Based on the audio format, the user also has to choose the right file extension.

    # Optional parameters:
    speed=None):

    # Checked: all, order, named, falsy
    # Meaning: all parameters in the API reference are supported, their order is natural,
    #     the parameters are specified with their names and potentially falsy values are converted to None.

    # The API offers more parameters like: extra_headers, extra_query, extra_body and timeout.
    # We wont support them because, in a situation where we need to specify them, we wont use one-liners.

    args = collections.PotentiallyFalsyArgs()
    args.must_contain("input", input)
    args.must_contain_enum_value("model", model)
    args.must_contain_enum_value("voice", voice)
    args.must_contain_enum_value("response_format", response_format)
    args.may_contain("speed", speed)

    with openai_client.audio.speech.with_streaming_response.create(**args.args) as response:
        file_system.create_parent_directory(file_path)
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
    # Input:
    file_path,

    # Parameters:
    model: OpenAiModel,
    response_format: OpenAiTranscriptFormat,

    # Optional parameters:
    language=None,
    prompt=None,
    temperature=None,
    timestamp_granularities=None):

    with open(file_path, "rb") as file:
        # Checked: all, order, named, falsy

        args = collections.PotentiallyFalsyArgs()
        args.must_contain("file", file)
        args.must_contain_enum_value("model", model)
        args.must_contain_enum_value("response_format", response_format)
        args.may_contain("language", language)
        args.may_contain("prompt", prompt)
        args.may_contain("temperature", temperature)
        args.may_contain("timestamp_granularities", timestamp_granularities)

        return openai_client.audio.transcriptions.create(**args.args)

def openai_audio_translations_create(
    # Input:
    file_path,

    # Parameters:
    model: OpenAiModel,
    response_format: OpenAiTranscriptFormat,

    # Optional parameters:
    prompt=None,
    temperature=None):

    with open(file_path, "rb") as file:
        # Checked: all, order, named, falsy

        args = collections.PotentiallyFalsyArgs()
        args.must_contain("file", file)
        args.must_contain_enum_value("model", model)
        args.must_contain_enum_value("response_format", response_format)
        args.may_contain("prompt", prompt)
        args.may_contain("temperature", temperature)

        return openai_client.audio.translations.create(**args.args)

# ------------------------------------------------------------------------------
#     Create image
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/guides/images
# https://platform.openai.com/docs/api-reference/images/create
# https://github.com/openai/openai-python/blob/main/src/openai/resources/images.py

class OpenAiImageQuality(enum.Enum):
    HD = "hd"
    STANDARD = "standard"

class OpenAiImageSize(enum.Enum):
    _256X256 = "256x256"
    _512X512 = "512x512"
    _1024X1024 = "1024x1024"
    _1792X1024 = "1792x1024"
    _1024X1792 = "1024x1792"

class OpenAiImageStyle(enum.Enum):
    NATURAL = "natural"
    VIVID = "vivid"

# Used internally.
# It's more like how the image is returned, but I like the simplicity of the name.
class OpenAiImageFormat(enum.Enum):
    B64_JSON = "b64_json"
    URL = "url"

def openai_images_generate_and_write(
    # Output:
    file_path,

    # Parameters:
    model: OpenAiModel,
    prompt,

    # Optional parameters:
    n=None,
    quality: OpenAiImageQuality=None,
    size: OpenAiImageSize=None,
    style: OpenAiImageStyle=None,
    user=None):
    ''' Returns a list of file paths. '''

    file_paths = []

    dirname = pyddle_path.dirname(file_path)
    basename = pyddle_path.basename(file_path)
    root, extension = os.path.splitext(basename)

    # Checked: all, order, named, falsy

    args = collections.PotentiallyFalsyArgs()
    args.must_contain_enum_value("model", model)
    args.must_contain("prompt", prompt)
    args.may_contain("n", n)
    args.may_contain_enum_value("quality", quality)
    args.may_contain_enum_value("size", size)
    args.may_contain_enum_value("style", style)
    args.may_contain("user", user)

    # This is a one-liner.
    # It takes care of saving the images as well.
    args.must_contain_enum_value("response_format", OpenAiImageFormat.URL)

    response = openai_client.images.generate(**args.args)

    # https://github.com/openai/openai-python/blob/main/src/openai/types/images_response.py
    # https://github.com/openai/openai-python/blob/main/src/openai/types/image.py

    for index, image in enumerate(response.data):
        if index == 0:
            new_file_path = file_path

        else:
            new_file_path = os.path.join(dirname, f"{root}-{index}{extension}")

        with requests.get(image.url, stream=True) as downloader:
            # If it fails with the second image, the user might leave the first one on the disk.
            # I will not take care of that for 2 reasons:
            #     1. If the first one was saved, the rest should usually be saved as well
            #     2. DALL-E-3 can generate only 1 image at a time
            downloader.raise_for_status()

            file_system.create_parent_directory(new_file_path)

            with open(new_file_path, "wb") as file:
                # I've seen 8192 in a lot of places.
                # https://stackoverflow.com/questions/2811006/what-is-a-good-buffer-size-for-socket-programming
                for chunk in downloader.iter_content(chunk_size=8192):
                    file.write(chunk)

        file_paths.append(new_file_path)

    return file_paths
