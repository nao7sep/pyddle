# Created: 2024-04-02
# Web-related things.

# ------------------------------------------------------------------------------
#     Timeouts
# ------------------------------------------------------------------------------

# OpenAI's Python API uses HTTPX's Timeout class.
# The default values are initialized as:
#     DEFAULT_TIMEOUT = httpx.Timeout(timeout=600.0, connect=5.0)
# https://www.python-httpx.org/advanced/timeouts/
# https://github.com/openai/openai-python/blob/main/src/openai/_constants.py

# The HTTPX's page above explains about its connect, read, write, pool timeouts.
# "pool" is for the time to wait for a connection from the connection pool.

# The Timeout class is defined in:
# https://github.com/encode/httpx/blob/master/httpx/_config.py
# That's also where we see HTTPX's default values:
#     DEFAULT_TIMEOUT_CONFIG = Timeout(timeout=5.0)

# OpenAI's sample code also contains:
#     client = OpenAI(
#         # 20 seconds (default is 10 minutes)
#         timeout=20.0,
#     )
# https://github.com/openai/openai-python/blob/main/README.md#timeouts

# ChatGPT says:
#     Start with Reasonable Defaults: A common starting point for many applications is a timeout of 5-10 seconds.
#     This is usually long enough to accommodate slow server responses under normal conditions but short enough to avoid excessive waiting for a response.

# GitHub Copilot often suggests 10 seconds.

# So, we can probably say:
#     * 4 values should be enough for timeouts
#     * Just because OpenAI's default is 10 minutes, doesnt mean the API wont work well with values like 20 seconds => Appears to be wrong
#     * Considering the values above and leaning towards the safer side, 10 seconds for each should be a good starting point

# Added: So, OpenAI's API doesnt work too well with 10 seconds not only when the entire message is returned at once but also when chunks are returned little by little.
# Sometimes, the Chat Completions API nearly freezes and doesnt return anything for (a lot) more than 10 seconds.
# Probably, it'd be better design to prepare the default timeout values for each module.
# OpenAI's values will be defined in pyddle_openai.py.

DEFAULT_TIMEOUT = 10
