# Created: 2024-03-07
# This script contains datetime-related utility functions.

import datetime

def get_utc_now():
    return datetime.datetime.now(datetime.UTC)

def utc_to_roundtrip_string(utc):
    """ Returns something like "2024-03-14T03:58:10.292580+00:00". """

    return utc.isoformat()

def roundtrip_string_to_utc(str_):
    return datetime.datetime.fromisoformat(str_)

# In .NET, I use code like ToString ("yyyyMMdd'T'HHmmss'-'fffffffK", CultureInfo.InvariantCulture) to generate an UTC timestamp that is able to roundtrip.
# I get strings like: "20240307T074742-5919023Z".
# With the following Python datetime format, we'll get strings like: "20240307T075556-212728Z", where the microseconds part is just one digit shorter.

# Added: 2024-04-22
# I changed the location of the UTC timezone indicator to preserve the consistency with the ISO 8601 format.
# Even with a millisecond-level part attached, the core part should still comply with the format.
# And, I also removed the then-redundant hyphen that separated the core part and the millisecond-level part.

# https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
ROUNDTRIP_FILE_NAME_STRING_FORMAT = '%Y%m%dT%H%M%SZ%f'

def utc_to_roundtrip_file_name_string(utc):
    """ Returns something like "20240307T075556Z212728". """

    return utc.strftime(ROUNDTRIP_FILE_NAME_STRING_FORMAT)
