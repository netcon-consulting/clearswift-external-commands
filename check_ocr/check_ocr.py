# check_ocr.py V3.1.0
#
# Copyright (c) 2022-2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from re import compile, search, IGNORECASE
from io import BytesIO
from PIL import Image
from pytesseract import image_to_string

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "regex_blacklist", "regex_whitelist", "size_min", "size_max", "skip_unsupported" )

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Check text in pictures against regular expression blacklist.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    :type disable_splitting: bool
    :type reformat_header: bool
    """
    try:
        with open(input, "rb") as f:
            image = f.read()
    except Exception:
        write_log(log, f"Cannot read image '{input}'")

        return ReturnCode.ERROR

    try:
        image = Image.open(BytesIO(image))
    except Exception:
        if config.skip_unsupported:
            return ReturnCode.NONE

        write_log(log, "Unsupported image format")

        return ReturnCode.ERROR

    if image.width < config.size_min or image.width > config.size_max or image.height < config.size_min or image.height > config.size_max:
        return ReturnCode.NONE

    try:
        set_blacklist = set(lexical_list(config.regex_blacklist))
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    set_blacklist = { compile(regex, IGNORECASE) for regex in set_blacklist }

    if config.regex_whitelist:
        try:
            set_whitelist = set(lexical_list(config.regex_whitelist))
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.ERROR

        set_whitelist = { compile(regex, IGNORECASE) for regex in set_whitelist }

    try:
        text = image_to_string(image, lang="eng+deu")
    except TypeError as ex:
        if not config.skip_unsupported:
            write_log(log, ex)

            return ReturnCode.ERROR
    else:
        if text:
            if config.regex_whitelist:
                for pattern in set_whitelist:
                    if search(pattern, text) is not None:
                        return ReturnCode.NONE

            for pattern in set_blacklist:
                if search(pattern, text) is not None:
                    write_log(log, pattern.pattern)

                    return ReturnCode.DETECTED

    return ReturnCode.NONE
