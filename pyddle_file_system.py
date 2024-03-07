# Created: 2024-02-29
# This script contains file-system-related functions.

import os
import pyddle_string as string

def make_and_move_to_output_subdirectory():
    # Supposing this module is in a subdirectory of the project's root directory.
    output_directory_path = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_directory_path, exist_ok=True)
    os.chdir(output_directory_path)

# ------------------------------------------------------------------------------
#     UTF encodings
# ------------------------------------------------------------------------------

# https://en.wikipedia.org/wiki/Byte_order_mark

# The following encodings and some others are not supported here.
# https://en.wikipedia.org/wiki/UTF-7
# https://en.wikipedia.org/wiki/UTF-1

utf_encodings_and_boms = {
    # Names must be in uppercase.
    ("UTF-8", b"\xEF\xBB\xBF"),
    ("UTF-16BE", b"\xFE\xFF"),
    ("UTF-16LE", b"\xFF\xFE"),
    ("UTF-32BE", b"\x00\x00\xFE\xFF"),
    ("UTF-32LE", b"\xFF\xFE\x00\x00"),
}

def get_utf_encoding_bom(encoding):
    uppercase_encoding = encoding.upper()

    for encoding, bom in utf_encodings_and_boms:
        if string.equals(encoding, uppercase_encoding):
            return bom

def write_utf_encoding_bom_to_file(file, encoding):
    bom = get_utf_encoding_bom(encoding)

    if bom:
        file.write(bom)

def detect_utf_encoding(bytes):
    for encoding, bom in utf_encodings_and_boms:
        if bytes.startswith(bom):
            return encoding, bom

    return None, None

def detect_utf_encoding_of_file(file):
    position = file.tell()
    bytes = file.read(4)
    encoding, bom = detect_utf_encoding(bytes)

    if encoding:
        file.seek(position + len(bom))

    else:
        # If the encoding isnt detected, the position goes back to where it was.
        file.seek(position)

    return encoding, bom

def open_file_and_write_utf_encoding_bom(path, encoding="UTF-8", append=False):
    bom = get_utf_encoding_bom(encoding)

    if not bom:
        # Here, we cant ignore this because writing the BOM is the whole point.
        raise ValueError(f"Unsupported encoding: {encoding}")

    if not append:
        file = open(path, "w", encoding=encoding)
        file.buffer.write(bom) # Using the underlying buffer.

    else:
        file = open(path, "a", encoding=encoding)
        file.buffer.seek(0, os.SEEK_END) # Just to make sure.

        if file.buffer.tell() == 0:
            file.buffer.write(bom)

    return file

def open_file_and_detect_utf_encoding(path, fallback_encoding="UTF-8"):
    file = open(path, "r", encoding="UTF-8") # The strongly encouraged default encoding.
    encoding, bom = detect_utf_encoding_of_file(file.buffer)

    if encoding:
        if string.equals_ignore_case(encoding, "UTF-8"):
            # The position should be right after the BOM.
            return file

        else:
            file.close()
            file = open(path, "r", encoding=encoding)
            # Adjust the position to be right after the BOM.
            file.buffer.seek(len(bom))
            return file

    else:
        if string.equals_ignore_case(fallback_encoding, "UTF-8"):
            # The position should be at the beginning of the file.
            return file

        else:
            file.close()
            file = open(path, "r", encoding=fallback_encoding)
            # No position adjustment is necessary.
            return file

# ------------------------------------------------------------------------------
#     All-at-once operations
# ------------------------------------------------------------------------------

def read_all_bytes_from_file(path):
    with open(path, "rb") as file:
        return file.read()

def read_all_text_from_file(path, detect_encoding=True, fallback_encoding="UTF-8"):
    if detect_encoding:
        with open_file_and_detect_utf_encoding(path, fallback_encoding) as file:
            return file.read()

    else:
        with open(path, "r", encoding=fallback_encoding) as file:
            return file.read()

def write_all_bytes_to_file(path, bytes):
    with open(path, "wb") as file:
        file.write(bytes)

def write_all_text_to_file(path, text, encoding="UTF-8", write_bom=True):
    if write_bom:
        with open_file_and_write_utf_encoding_bom(path, encoding) as file:
            file.write(text)

    else:
        with open(path, "w", encoding=encoding) as file:
            file.write(text)

def append_all_bytes_to_file(path, bytes):
    with open(path, "ab") as file:
        file.write(bytes)

def append_all_text_to_file(path, text, encoding="UTF-8", write_bom=True):
    if write_bom:
        with open_file_and_write_utf_encoding_bom(path, encoding, append=True) as file:
            file.write(text)

    else:
        with open(path, "a", encoding=encoding) as file:
            file.write(text)
