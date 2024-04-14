# Created: 2024-03-26
# Sugar-coating classes and methods for OpenAI's API.

import base64
import enum
import mimetypes
import os
import requests
import tiktoken

import httpx
import openai
import openai.types.chat

import pyddle_collections as pcollections
import pyddle_json_based_kvs as pkvs
import pyddle_file_system as pfs
import pyddle_path as ppath
import pyddle_utility as putility
import pyddle_web as pweb

# This script contains some one-liners.
# I will keep their names simple and stupid because I might want to add more later.

# ------------------------------------------------------------------------------
#     Constants
# ------------------------------------------------------------------------------

DEFAULT_TIMEOUT = pweb.DEFAULT_TIMEOUT
DEFAULT_RESPONSE_TIMEOUT = pweb.DEFAULT_TIMEOUT * 5 * 5
DEFAULT_CHUNK_TIMEOUT = pweb.DEFAULT_TIMEOUT * 5

# ------------------------------------------------------------------------------
#     Settings
# ------------------------------------------------------------------------------

KVS_KEY_PREFIX = "pyddle_openai/"

# https://platform.openai.com/docs/api-reference
# https://platform.openai.com/docs/guides/production-best-practices

class OpenAiSettings:
    def __init__(self, kvs_data, kvs_key_prefix):
        self.kvs_data = kvs_data
        self.kvs_key_prefix = kvs_key_prefix

        # Optional:
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

# Lazy loading:
__openai_default_settings: OpenAiSettings | None = None # pylint: disable = invalid-name

def get_openai_default_settings():
    global __openai_default_settings # pylint: disable = global-statement

    if __openai_default_settings is None:
        __openai_default_settings = OpenAiSettings(
            kvs_data = pkvs.get_merged_kvs_data(),
            kvs_key_prefix = KVS_KEY_PREFIX)

    return __openai_default_settings

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

    def encode(self, str_):
        ''' Returns a list of tokens as integers. '''

        return self.encoding.encode(str_)

    def count(self, str_):
        ''' Returns the number of tokens. '''

        return len(self.encode(str_))

    def encode_to_strs(self, str_):
        ''' Returns a list of tokens as decoded strings. OFTEN fails to decode CJK strings. '''

        # If we specify "ignore" or "replace" as the "errors" argument, we can avoid the UnicodeDecodeError,
        #     but the fundamental problem is that the string representation as UTF-8-decoded byte arrays are then cut into tokens with no consideration of the character boundaries,
        #     and therefore there's not much point in just making the method work when half the CJK characters anyway disappear.
        return [self.encoding.decode_single_token_bytes(token).decode("utf-8") for token in self.encode(str_)]

# Lazy loading:
__gpt_3_5_turbo_token_counter: OpenAiTokenCounter | None = None # pylint: disable = invalid-name

def get_gpt_3_5_turbo_token_counter():
    global __gpt_3_5_turbo_token_counter # pylint: disable = global-statement

    if __gpt_3_5_turbo_token_counter is None:
        __gpt_3_5_turbo_token_counter = OpenAiTokenCounter(model = OpenAiModel.GPT_3_5_TURBO)

    return __gpt_3_5_turbo_token_counter

# Lazy loading:
__gpt_4_token_counter: OpenAiTokenCounter | None = None # pylint: disable = invalid-name

def get_gpt_4_token_counter():
    global __gpt_4_token_counter # pylint: disable = global-statement

    if __gpt_4_token_counter is None:
        __gpt_4_token_counter = OpenAiTokenCounter(model = OpenAiModel.GPT_4)

    return __gpt_4_token_counter

# Lazy loading:
__gpt_4_turbo_token_counter: OpenAiTokenCounter | None = None # pylint: disable = invalid-name

def get_gpt_4_turbo_token_counter():
    global __gpt_4_turbo_token_counter # pylint: disable = global-statement

    if __gpt_4_turbo_token_counter is None:
        __gpt_4_turbo_token_counter = OpenAiTokenCounter(model = OpenAiModel.GPT_4_TURBO)

    return __gpt_4_turbo_token_counter

# Lazy loading:
# May be unnecessary.
__gpt_4_vision_token_counter: OpenAiTokenCounter | None = None # pylint: disable = invalid-name

def get_gpt_4_vision_token_counter():
    global __gpt_4_vision_token_counter # pylint: disable = global-statement

    if __gpt_4_vision_token_counter is None:
        __gpt_4_vision_token_counter = OpenAiTokenCounter(model = OpenAiModel.GPT_4_VISION)

    return __gpt_4_vision_token_counter

# Lazy loading:
__openai_default_token_counter: OpenAiTokenCounter | None = None # pylint: disable = invalid-name

def get_openai_default_token_counter():
    global __openai_default_token_counter # pylint: disable = global-statement

    if __openai_default_token_counter is None:
        if DEFAULT_GPT_MODEL == OpenAiModel.GPT_3_5_TURBO:
            __openai_default_token_counter = get_gpt_3_5_turbo_token_counter()

        elif DEFAULT_GPT_MODEL == OpenAiModel.GPT_4:
            __openai_default_token_counter = get_gpt_4_token_counter()

        elif DEFAULT_GPT_MODEL == OpenAiModel.GPT_4_TURBO:
            __openai_default_token_counter = get_gpt_4_turbo_token_counter()

        elif DEFAULT_GPT_MODEL == OpenAiModel.GPT_4_VISION:
            __openai_default_token_counter = get_gpt_4_vision_token_counter()

        else:
            raise RuntimeError(f"Unsupported model: {DEFAULT_GPT_MODEL}")

    return __openai_default_token_counter

# ------------------------------------------------------------------------------
#     Clients
# ------------------------------------------------------------------------------

# https://github.com/openai/openai-python/blob/main/src/openai/_client.py

def create_openai_client(api_key = None, organization = None, base_url = None, timeout = None):
    ''' If the arguments are falsy and cant be retrieved from "get_openai_default_settings", environment variables (where the keys are "OPENAI_API_KEY", "OPENAI_ORG_ID" and "OPENAI_BASE_URL") are used internally. '''

    if not api_key:
        api_key = get_openai_default_settings().api_key

    if not organization:
        organization = get_openai_default_settings().organization

    if not base_url:
        base_url = get_openai_default_settings().base_url

    args = pcollections.PotentiallyFalsyArgs()
    args.may_contain("api_key", api_key)
    args.may_contain("organization", organization)
    args.may_contain("base_url", base_url)

    if timeout:
        args.must_contain("timeout", timeout)

    else:
        # Explained in pyddle_web.py.
        args.must_contain("timeout", httpx.Timeout(timeout = pweb.DEFAULT_TIMEOUT, read = DEFAULT_RESPONSE_TIMEOUT))

    return openai.OpenAI(**args.args)

# Lazy loading:
__openai_default_client: openai.OpenAI | None = None # pylint: disable = invalid-name

def get_openai_default_client():
    global __openai_default_client # pylint: disable = global-statement

    if __openai_default_client is None:
        __openai_default_client = create_openai_client()

    return __openai_default_client

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

def openai_audio_speech_create(
    # Input:
    input_,

    # Parameters:
    model: OpenAiModel,
    voice: OpenAiVoice,
    response_format: OpenAiAudioFormat, # Defaults to "mp3" in the API, but the user should specify one.
    # Based on the audio format, the user also has to choose the right file extension.

    # Optional parameters:
    speed = None,

    # Optional settings:
    client: openai.OpenAI | None = None,
    timeout = None):

    # Checked: all, order, named, falsy
    # Meaning: all parameters in the API reference are supported, their order is natural,
    #     the parameters are specified with their names and potentially falsy values are converted to None.

    # The API offers more parameters like: extra_headers, extra_query, extra_body and timeout.
    # We wont support them because, in a situation where we need to specify them, we wont use one-liners.

    args = pcollections.PotentiallyFalsyArgs()
    args.must_contain("input", input_)
    args.must_contain_enum_value("model", model)
    args.must_contain_enum_value("voice", voice)
    args.must_contain_enum_value("response_format", response_format)
    args.may_contain("speed", speed)

    if timeout:
        args.must_contain("timeout", timeout)

    # "create" returns HttpxBinaryResponseContent.
    # https://github.com/openai/openai-python/blob/main/src/openai/_legacy_response.py
    return putility.get_not_none_or_call_func(get_openai_default_client, client).audio.speech.create(**args.args) # pylint: disable = missing-kwoa

def openai_save_audio(file_path, response):
    pfs.create_parent_directory(file_path)
    response.write_to_file(file_path)

# ------------------------------------------------------------------------------
#     Speech to text
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/guides/speech-to-text
# https://platform.openai.com/docs/api-reference/audio/createTranscription
# https://platform.openai.com/docs/api-reference/audio/createTranslation
# https://github.com/openai/openai-python/blob/main/src/openai/resources/audio/transcriptions.py
# https://github.com/openai/openai-python/blob/main/src/openai/resources/audio/translations.py

# Below is a list of supported languages by Whisper, NOT the GPT models.
# Whisper is a "general-purpose speech recognition model".
# As of 2024-04-04, I cant seem to find any official list for the GPT models.
# As major languages are in the list and the names seem to be consistent with the ISO 639-1 codes,
#     it shouldnt hurt to use the enum values for the GPT models as well.
# https://platform.openai.com/docs/guides/text-to-speech
# https://github.com/openai/whisper#available-models-and-languages
# https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes

# The rest of the comments have become "episodic" and been moved to: RK32 OpenAI Supported Languages.json

class OpenAiLanguage(enum.Enum):
    AFRIKAANS = "afrikaans"
    ARABIC = "arabic"
    ARMENIAN = "armenian"
    AZERBAIJANI = "azerbaijani"
    BELARUSIAN = "belarusian"
    BOSNIAN = "bosnian"
    BULGARIAN = "bulgarian"
    CATALAN = "catalan"
    CHINESE = "chinese"
    CROATIAN = "croatian"
    CZECH = "czech"
    DANISH = "danish"
    DUTCH = "dutch"
    ENGLISH = "english"
    ESTONIAN = "estonian"
    FINNISH = "finnish"
    FRENCH = "french"
    GALICIAN = "galician"
    GERMAN = "german"
    GREEK = "greek"
    HEBREW = "hebrew"
    HINDI = "hindi"
    HUNGARIAN = "hungarian"
    ICELANDIC = "icelandic"
    INDONESIAN = "indonesian"
    ITALIAN = "italian"
    JAPANESE = "japanese"
    KANNADA = "kannada"
    KAZAKH = "kazakh"
    KOREAN = "korean"
    LATVIAN = "latvian"
    LITHUANIAN = "lithuanian"
    MACEDONIAN = "macedonian"
    MALAY = "malay"
    MARATHI = "marathi"
    MAORI = "maori"
    NEPALI = "nepali"
    NORWEGIAN = "norwegian"
    PERSIAN = "persian"
    POLISH = "polish"
    PORTUGUESE = "portuguese"
    ROMANIAN = "romanian"
    RUSSIAN = "russian"
    SERBIAN = "serbian"
    SLOVAK = "slovak"
    SLOVENIAN = "slovenian"
    SPANISH = "spanish"
    SWAHILI = "swahili"
    SWEDISH = "swedish"
    TAGALOG = "tagalog"
    TAMIL = "tamil"
    THAI = "thai"
    TURKISH = "turkish"
    UKRAINIAN = "ukrainian"
    URDU = "urdu"
    VIETNAMESE = "vietnamese"
    WELSH = "welsh"

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
    language = None,
    prompt = None,
    temperature = None,
    timestamp_granularities = None,

    # Optional settings:
    client: openai.OpenAI | None = None,
    timeout = None):

    with open(file_path, "rb") as file:
        # Checked: all, order, named, falsy

        args = pcollections.PotentiallyFalsyArgs()
        args.must_contain("file", file)
        args.must_contain_enum_value("model", model)
        args.must_contain_enum_value("response_format", response_format)
        args.may_contain("language", language)
        args.may_contain("prompt", prompt)
        args.may_contain("temperature", temperature)
        args.may_contain("timestamp_granularities", timestamp_granularities)

        if timeout:
            args.must_contain("timeout", timeout)

        return putility.get_not_none_or_call_func(get_openai_default_client, client).audio.transcriptions.create(**args.args) # pylint: disable = missing-kwoa

def openai_audio_translations_create(
    # Input:
    file_path,

    # Parameters:
    model: OpenAiModel,
    # Using the same enum type.
    # Audio translation is basically transcription + translation.
    response_format: OpenAiTranscriptFormat,

    # Optional parameters:
    prompt = None,
    temperature = None,

    # Optional settings:
    client: openai.OpenAI | None = None,
    timeout = None):

    with open(file_path, "rb") as file:
        # Checked: all, order, named, falsy

        args = pcollections.PotentiallyFalsyArgs()
        args.must_contain("file", file)
        args.must_contain_enum_value("model", model)
        args.must_contain_enum_value("response_format", response_format)
        args.may_contain("prompt", prompt)
        args.may_contain("temperature", temperature)

        if timeout:
            args.must_contain("timeout", timeout)

        return putility.get_not_none_or_call_func(get_openai_default_client, client).audio.translations.create(**args.args) # pylint: disable = missing-kwoa

# ------------------------------------------------------------------------------
#     Chat
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/guides/chat
# https://platform.openai.com/docs/api-reference/chat
# https://github.com/openai/openai-python/blob/main/src/openai/resources/chat/completions.py

# I wont be supporting tools or anything related to them for now.
# Just like assistants, they must be useful in certain situations, but I currently dont need them.
# https://platform.openai.com/docs/api-reference/assistants

class OpenAiRole(enum.Enum):
    ASSISTANT = "assistant"
    SYSTEM = "system"
    USER = "user"

class OpenAiChatFormat(enum.Enum):
    JSON_OBJECT = "json_object"
    TEXT = "text"

def openai_chat_completions_create(
    # Parameters:
    model: OpenAiModel,
    messages,

    # Optional parameters:
    # In order of appearance in the API reference.
    frequency_penalty = None,
    logit_bias = None,
    logprobs = None,
    top_logprobs = None,
    max_tokens = None,
    n = None,
    presence_penalty = None,
    response_format: OpenAiChatFormat | None = None,
    seed = None,
    stop = None,
    stream = None,
    temperature = None,
    top_p = None,
    user = None,

    # Optional settings:
    client: openai.OpenAI | None = None,
    timeout = None):

    # Checked: all, order, named, falsy

    args = pcollections.PotentiallyFalsyArgs()
    args.must_contain_enum_value("model", model)
    args.must_contain("messages", messages)
    args.may_contain("frequency_penalty", frequency_penalty)
    args.may_contain("logit_bias", logit_bias)
    args.may_contain("logprobs", logprobs)
    args.may_contain("top_logprobs", top_logprobs)
    args.may_contain("max_tokens", max_tokens)
    args.may_contain("n", n)
    args.may_contain("presence_penalty", presence_penalty)
    args.may_contain_enum_value("response_format", response_format)
    args.may_contain("seed", seed)
    args.may_contain("stop", stop)
    args.may_contain("stream", stream)
    args.may_contain("temperature", temperature)
    args.may_contain("top_p", top_p)
    args.may_contain("user", user)

    if timeout:
        args.must_contain("timeout", timeout)

    else:
        if stream:
            args.must_contain("timeout", httpx.Timeout(timeout = pweb.DEFAULT_TIMEOUT, read = DEFAULT_CHUNK_TIMEOUT))

    return putility.get_not_none_or_call_func(get_openai_default_client, client).chat.completions.create(**args.args)

class OpenAiChatSettings:
    def __init__(self, model: OpenAiModel):
        self.model: OpenAiModel = model

        # Optional:
        self.frequency_penalty = None
        self.logit_bias = None
        self.logprobs = None
        self.top_logprobs = None
        self.max_tokens = None
        self.n = None
        self.presence_penalty = None
        self.response_format: OpenAiChatFormat | None = None
        self.seed = None
        self.stop = None
        self.stream = None
        self.temperature = None
        self.top_p = None
        self.user = None

# Let's go for the model we'd normally choose if we could choose any.

# As of 2024-04-04, GPT 3.5 Turbo is the one used in the example in the API reference,
#     and it's inexpensive and just enough for many kinds of work,
#     but the training data is from 2021 and the context window is limited.
# https://platform.openai.com/docs/api-reference/chat/create

# When we use a GPT model for work, we usually care about quality rather than quantity.

DEFAULT_GPT_MODEL = OpenAiModel.GPT_4_TURBO

# Lazy loading:
__openai_default_chat_settings: OpenAiChatSettings | None = None # pylint: disable = invalid-name

def get_openai_default_chat_settings():
    global __openai_default_chat_settings # pylint: disable = global-statement

    if __openai_default_chat_settings is None:
        __openai_default_chat_settings = OpenAiChatSettings(model = DEFAULT_GPT_MODEL)

    return __openai_default_chat_settings

def openai_chat_completions_create_with_settings(
    settings: OpenAiChatSettings,
    messages,

    # Optional settings:
    client: openai.OpenAI | None = None,
    stream_override = None,
    timeout = None):

    return openai_chat_completions_create(
        model = settings.model,
        messages = messages,
        frequency_penalty = settings.frequency_penalty,
        logit_bias = settings.logit_bias,
        logprobs = settings.logprobs,
        top_logprobs = settings.top_logprobs,
        max_tokens = settings.max_tokens,
        n = settings.n,
        presence_penalty = settings.presence_penalty,
        response_format = settings.response_format,
        seed = settings.seed,
        stop = settings.stop,
        stream = settings.stream if stream_override is None else stream_override,
        temperature = settings.temperature,
        top_p = settings.top_p,
        user = settings.user,
        client = client,
        timeout = timeout)

def openai_build_message(role: OpenAiRole, content, name = None):
    message = {}

    if name:
        # "name" is optional, but it'd be more intuitive to have it in this order.
        message["name"] = name

    message["role"] = role.value
    message["content"] = content

    return message

def openai_add_message(messages, role: OpenAiRole, content, name = None):
    messages.append(openai_build_message(role = role, content = content, name = name))

def openai_add_system_message(messages, system_message, name = None):
    openai_add_message(messages, role = OpenAiRole.SYSTEM, content = system_message, name = name)

def openai_add_user_message(messages, user_message, name = None):
    openai_add_message(messages, role = OpenAiRole.USER, content = user_message, name = name)

def openai_add_assistant_message(messages, assistant_message, name = None):
    openai_add_message(messages, role = OpenAiRole.ASSISTANT, content = assistant_message, name = name)

def openai_build_messages(user_message, user_message_name = None, system_message = None, system_message_name = None):
    messages = []

    if system_message:
        openai_add_system_message(messages, system_message, system_message_name)

    openai_add_user_message(messages, user_message, user_message_name)

    return messages

def openai_extract_messages(response: openai.types.chat.ChatCompletion):
    return [choice.message.content for choice in response.choices]

def openai_extract_first_message(response: openai.types.chat.ChatCompletion):
    return response.choices[0].message.content

def openai_extract_deltas(response: openai.types.chat.ChatCompletion):
    return [choice.delta.content for choice in response.choices]

def openai_extract_first_delta(chunk: openai.types.chat.ChatCompletionChunk):
    return chunk.choices[0].delta.content

# ------------------------------------------------------------------------------
#     Vision
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/guides/vision

class OpenAiVisionDetail(enum.Enum):
    AUTO = "auto"
    HIGH = "high"
    LOW = "low"

def openai_build_messages_for_vision(image_file_paths, user_message,
                                     detail: OpenAiVisionDetail | None = None,
                                     system_message = None):
    messages = []

    if system_message:
        messages.append({
            "role": OpenAiRole.SYSTEM.value,
            "content": system_message
        })

    content = []

    content.append({
        "type": "text",
        "text": user_message
    })

    for image_file_path in image_file_paths:
        with open(image_file_path, "rb") as image_file:
            # https://docs.python.org/3/library/mimetypes.html
            mimetype = mimetypes.guess_type(image_file_path)[0]
            # https://docs.python.org/3/library/base64.html
            base64_str = base64.b64encode(image_file.read()).decode("ascii")

            image_url = {}

            image_url["url"] = f"data:{mimetype};base64,{base64_str}"

            if detail:
                image_url["detail"] = detail.value

            content.append({
                "type": "image_url",
                "image_url": image_url
            })

    messages.append({
        "role": OpenAiRole.USER.value,
        "content": content
    })

    return messages

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
    # The only way to start the names with numbers without adding meanings.
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

def openai_save_images(file_path, response):
    ''' Returns a list of file paths. '''

    file_paths = []

    dirname = ppath.dirname(file_path)
    basename = ppath.basename(file_path)
    root, extension = os.path.splitext(basename)

    # https://github.com/openai/openai-python/blob/main/src/openai/types/images_response.py
    # https://github.com/openai/openai-python/blob/main/src/openai/types/image.py

    for index, image in enumerate(response.data):
        if index == 0:
            new_file_path = file_path

        else:
            new_file_path = os.path.join(dirname, f"{root}-{index}{extension}")

        with requests.get(image.url, stream = True, timeout = pweb.DEFAULT_TIMEOUT) as downloader:
            # If it fails with the second image, the user might leave the first one on the disk.
            # I will not take care of that for 2 reasons:
            #     1. If the first one was saved, the rest should usually be saved as well
            #     2. DALL-E-3 can generate only 1 image at a time
            downloader.raise_for_status()

            pfs.create_parent_directory(new_file_path)

            with open(new_file_path, "wb") as file:
                # I've seen 8192 in a lot of places.
                # https://stackoverflow.com/questions/2811006/what-is-a-good-buffer-size-for-socket-programming
                for chunk in downloader.iter_content(chunk_size = 8192):
                    file.write(chunk)

        file_paths.append(new_file_path)

    return file_paths

def openai_images_generate(
    # Parameters:
    model: OpenAiModel,
    prompt,

    # Optional parameters:
    n = None,
    quality: OpenAiImageQuality | None = None,
    size: OpenAiImageSize | None = None,
    style: OpenAiImageStyle | None = None,
    user = None,

    # Optional settings:
    client: openai.OpenAI | None = None,
    timeout = None):

    ''' Returns a list of file paths. '''

    # Checked: all, order, named, falsy

    args = pcollections.PotentiallyFalsyArgs()
    args.must_contain_enum_value("model", model)
    args.must_contain("prompt", prompt)
    args.may_contain("n", n)
    args.may_contain_enum_value("quality", quality)
    args.may_contain_enum_value("size", size)
    args.may_contain_enum_value("style", style)
    args.may_contain("user", user)

    if timeout:
        args.must_contain("timeout", timeout)

    # This is a one-liner.
    # It takes care of saving the images as well.
    args.must_contain_enum_value("response_format", OpenAiImageFormat.URL)

    return putility.get_not_none_or_call_func(get_openai_default_client, client).images.generate(**args.args) # pylint: disable = missing-kwoa

# ------------------------------------------------------------------------------
#     Create image edit
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/api-reference/images/createEdit

def openai_images_edit(
    # Input:
    input_file_path,

    # Parameters:
    model: OpenAiModel,
    prompt,

    # Optional parameters:
    mask_file_path = None,
    n = None,
    size: OpenAiImageSize | None = None,
    user = None,

    # Optional settings:
    client: openai.OpenAI | None = None,
    timeout = None):

    ''' Returns a list of file paths. '''

    with open(input_file_path, "rb") as input_file:
        # Checked: all, order, named, falsy

        args = pcollections.PotentiallyFalsyArgs()
        args.must_contain("image", input_file)
        args.must_contain_enum_value("model", model)
        args.must_contain("prompt", prompt)
        args.may_contain("n", n)
        args.may_contain_enum_value("size", size)
        args.may_contain("user", user)

        if timeout:
            args.must_contain("timeout", timeout)

        args.must_contain_enum_value("response_format", OpenAiImageFormat.URL)

        if mask_file_path:
            with open(mask_file_path, "rb") as mask_file:
                args.must_contain("mask", mask_file)

                return putility.get_not_none_or_call_func(get_openai_default_client, client).images.edit(**args.args) # pylint: disable = missing-kwoa

        else:
            return putility.get_not_none_or_call_func(get_openai_default_client, client).images.edit(**args.args) # pylint: disable = missing-kwoa

# ------------------------------------------------------------------------------
#     Create image variation
# ------------------------------------------------------------------------------

# https://platform.openai.com/docs/api-reference/images/createVariation

def openai_images_create_variation(
    # Input:
    input_file_path,

    # Parameters:
    model: OpenAiModel,

    # Optional parameters:
    n = None,
    size: OpenAiImageSize | None = None,
    user = None,

    # Optional settings:
    client: openai.OpenAI | None = None,
    timeout = None):

    ''' Returns a list of file paths. '''

    with open(input_file_path, "rb") as input_file:
        # Checked: all, order, named, falsy

        args = pcollections.PotentiallyFalsyArgs()
        args.must_contain("image", input_file)
        args.must_contain_enum_value("model", model)
        args.may_contain("n", n)
        args.may_contain_enum_value("size", size)
        args.may_contain("user", user)

        if timeout:
            args.must_contain("timeout", timeout)

        args.must_contain_enum_value("response_format", OpenAiImageFormat.URL)

        return putility.get_not_none_or_call_func(get_openai_default_client, client).images.create_variation(**args.args) # pylint: disable = missing-kwoa
