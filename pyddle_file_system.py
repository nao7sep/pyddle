﻿# Created: 2024-02-29
# This script contains file-system-related functions.

import os
import zipfile

import pyddle_errors as perrors
import pyddle_global as pglobal
import pyddle_path as ppath
import pyddle_string as pstring

def create_parent_directory(path):
    parent_directory_path = ppath.dirname(path)

    if parent_directory_path:
        os.makedirs(parent_directory_path, exist_ok = True)

def make_and_move_to_output_subdirectory(subdirectory = None):
    """ A lazy method that alters the current working directory and therefore must be used with caution. """

    # No lazy loading required.
    directory_path = os.path.join(ppath.dirname(pglobal.get_main_script_file_path()), "output")

    if subdirectory:
        directory_path = os.path.join(directory_path, subdirectory)

    os.makedirs(directory_path, exist_ok = True)
    os.chdir(directory_path)

# ------------------------------------------------------------------------------
#     UTF encodings
# ------------------------------------------------------------------------------

# https://en.wikipedia.org/wiki/Byte_order_mark

# The following encodings and some others are not supported here.
# https://en.wikipedia.org/wiki/UTF-7
# https://en.wikipedia.org/wiki/UTF-1

UTF_ENCODINGS_AND_BOMS = {
    # Names must be in uppercase.
    ("UTF-8", b"\xEF\xBB\xBF"),
    ("UTF-16BE", b"\xFE\xFF"),
    ("UTF-16LE", b"\xFF\xFE"),
    ("UTF-32BE", b"\x00\x00\xFE\xFF"),
    ("UTF-32LE", b"\xFF\xFE\x00\x00"),
}

def get_utf_encoding_bom(encoding):
    """ Returns None if the encoding is not supported. """

    uppercase_encoding = encoding.upper()

    for encoding, bom in UTF_ENCODINGS_AND_BOMS:
        if pstring.equals(encoding, uppercase_encoding):
            return bom

def write_utf_encoding_bom_to_file(file, encoding):
    """ Writes the BOM only if the encoding is supported. """

    bom = get_utf_encoding_bom(encoding)

    if bom:
        file.write(bom)

def detect_utf_encoding(bytes_):
    """ Returns (None, None) if the encoding is not detected. """

    for encoding, bom in UTF_ENCODINGS_AND_BOMS:
        if bytes_.startswith(bom):
            return encoding, bom

    return None, None

def detect_utf_encoding_of_file(file):
    """
        The position will be right after the detected BOM.
        Returns (None, None) if the encoding is not detected.
    """

    position = file.tell()
    bytes_ = file.read(4)
    encoding, bom = detect_utf_encoding(bytes_)

    if encoding:
        file.seek(position + len(bom))

    else:
        # If the encoding isnt detected, the position goes back to where it was.
        file.seek(position)

    return encoding, bom

def open_file_and_write_utf_encoding_bom(path, encoding = "UTF-8", append = False):
    """
        Raises an error if the encoding is not supported.
        If 'append' is True and the file already has content without a BOM, the BOM will NOT be written.
    """

    bom = get_utf_encoding_bom(encoding)

    if not bom:
        # Here, we cant ignore this because writing the BOM is the whole point.
        raise perrors.NotSupportedError(f"Unsupported encoding: {encoding}")

    if not append:
        file = open(path, "w", encoding = encoding)
        file.buffer.write(bom) # Using the underlying buffer.

    else:
        file = open(path, "a", encoding = encoding)
        file.buffer.seek(0, os.SEEK_END) # Just to make sure.

        if file.buffer.tell() == 0:
            file.buffer.write(bom)

    return file

def open_file_and_detect_utf_encoding(path, fallback_encoding = "UTF-8"):
    """ The position will be right after the detected BOM (if there's one). """

    file = open(path, "r", encoding = "UTF-8") # The strongly encouraged default encoding.
    encoding, bom = detect_utf_encoding_of_file(file.buffer)

    if encoding:
        if pstring.equals_ignore_case(encoding, "UTF-8"):
            # The position should be right after the BOM.
            return file

        else:
            file.close()
            file = open(path, "r", encoding = encoding)
            # Adjust the position to be right after the BOM.
            file.buffer.seek(len(bom))
            return file

    else:
        if pstring.equals_ignore_case(fallback_encoding, "UTF-8"):
            # The position should be at the beginning of the file.
            return file

        else:
            file.close()
            file = open(path, "r", encoding = fallback_encoding)
            # No position adjustment is necessary.
            return file

# ------------------------------------------------------------------------------
#     All-at-once operations
# ------------------------------------------------------------------------------

def read_all_bytes_from_file(path):
    with open(path, "rb") as file:
        return file.read()

def read_all_text_from_file(path, detect_encoding = True, fallback_encoding = "UTF-8"):
    if detect_encoding:
        with open_file_and_detect_utf_encoding(path, fallback_encoding) as file:
            return file.read()

    else:
        with open(path, "r", encoding = fallback_encoding) as file:
            return file.read()

def write_all_bytes_to_file(path, bytes_):
    with open(path, "wb") as file:
        file.write(bytes_)

def write_all_text_to_file(path, text, encoding = "UTF-8", write_bom = True):
    if write_bom:
        with open_file_and_write_utf_encoding_bom(path, encoding) as file:
            file.write(text)

    else:
        with open(path, "w", encoding = encoding) as file:
            file.write(text)

def append_all_bytes_to_file(path, bytes_):
    with open(path, "ab") as file:
        file.write(bytes_)

def append_all_text_to_file(path, text, encoding = "UTF-8", write_bom = True):
    """ If the file already has content without a BOM, the BOM will NOT be written. """

    if write_bom:
        with open_file_and_write_utf_encoding_bom(path, encoding, append = True) as file:
            file.write(text)

    else:
        with open(path, "a", encoding = encoding) as file:
            file.write(text)

# ------------------------------------------------------------------------------
#     ZIP archives
# ------------------------------------------------------------------------------

def zip_archive_directory(directory_path, archive_file_path, not_archived_directory_names = None, not_archived_file_names = None):
    archive_directory_path = ppath.dirname(archive_file_path)
    os.makedirs(archive_directory_path, exist_ok = True)

    # https://docs.python.org/3/library/zipfile.html

    with zipfile.ZipFile(archive_file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        if os.path.isdir(directory_path):
            return zip_archive_subdirectory(zip_file, directory_path, directory_path, not_archived_directory_names, not_archived_file_names)

def zip_archive_subdirectory(zip_file, root_directory_path, subdirectory_path, not_archived_directory_names, not_archived_file_names):
    archived_file_count = 0

    for name in os.listdir(subdirectory_path):
        path = os.path.join(subdirectory_path, name)

        if os.path.isdir(path):
            if not_archived_directory_names and pstring.contains_ignore_case(not_archived_directory_names, name):
                continue

            zip_archive_subdirectory(zip_file, root_directory_path, path, not_archived_directory_names, not_archived_file_names)

        elif os.path.isfile(path):
            if not_archived_file_names and pstring.contains_ignore_case(not_archived_file_names, name):
                continue

            # https://docs.python.org/3/library/os.path.html#os.path.relpath
            relative_file_path = os.path.relpath(path, root_directory_path)
            zip_file.write(path, relative_file_path)
            archived_file_count += 1

        else:
            # Other things such as symbolic links.
            raise perrors.NotSupportedError(f"Unsupported file system object: {path}")

    return archived_file_count
