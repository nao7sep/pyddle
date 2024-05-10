# Created: 2024-05-10
# Contains environment-related things.

import os

import pyddle_string as pstring

IS_NT = pstring.equals_ignore_case(os.name, 'nt')
IS_POSIX = pstring.equals_ignore_case(os.name, 'posix')
