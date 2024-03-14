# Created: 2024-03-07
# This script contains datetime-related utility functions.

import datetime

def get_utc_now():
    return datetime.datetime.now(datetime.UTC)

def utc_to_roundtrip_string(utc):
    """ Returns something like "2024-03-14T03:58:10.292580+00:00". """
    return utc.isoformat()

def roundtrip_string_to_utc(str):
    return datetime.datetime.fromisoformat(str)

# In .NET, I use code like ToString ("yyyyMMdd'T'HHmmss'-'fffffffK", CultureInfo.InvariantCulture) to generate an UTC timestamp that is able to roundtrip.
# I get strings like: "20240307T074742-5919023Z".
# With the following Python datetime format, we'll get strings like: "20240307T075556-212728Z", where the microseconds part is just one digit shorter.

# https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
roundtrip_file_name_string_format = '%Y%m%dT%H%M%S-%fZ'

def utc_to_roundtrip_file_name_string(utc):
    """ Returns something like "20240307T075556-212728Z". """
    return utc.strftime(roundtrip_file_name_string_format)
