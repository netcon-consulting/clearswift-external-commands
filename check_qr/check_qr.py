# check_qr.py V6.1.0
#
# Copyright (c) 2021-2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from re import compile, finditer, IGNORECASE
from PIL import Image
from pyzbar.pyzbar import decode

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "url_blacklist", "url_whitelist" )

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Check URLs from QR-codes in pictures against URL blacklist and corresponding domains against reputation blacklists.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    :type disable_splitting: bool
    :type reformat_header: bool
    """
    try:
        image = Image.open(input)
    except Exception:
        write_log(log, f"Cannot read image '{input}'")

        return ReturnCode.ERROR

    list_qr = decode(image)

    if list_qr:
        set_url = set()

        for qr_code in list_qr:
            try:
                set_url |= set(finditer(PATTERN_URL, qr_code.data.decode()))
            except Exception:
                pass

        if set_url:
            if config.url_blacklist:
                try:
                    set_blacklist = set(url_list(config.url_blacklist))
                except Exception as ex:
                    write_log(log, ex)

                    return ReturnCode.ERROR

                set_blacklist = { compile(url2regex(url), IGNORECASE) for url in set_blacklist }
            else:
                set_blacklist = None

            if config.url_whitelist:
                try:
                    set_whitelist = set(url_list(config.url_whitelist))
                except Exception as ex:
                    write_log(log, ex)

                    return ReturnCode.ERROR

                set_whitelist = { compile(url2regex(url), IGNORECASE) for url in set_whitelist }
            else:
                set_whitelist = None

            set_clean = set()

            for url in set_url:
                if url not in set_clean:
                    result = url_blacklisted(url, set_whitelist, set_blacklist)

                    if result is not None:
                        if result:
                            write_log(log, f"'{result[0]}' listed on '{result[1]}'")

                        write_log(log, f"'{url}' listed on '{config.url_blacklist}'")

                        return ReturnCode.DETECTED

                    set_clean.add(url)

    return ReturnCode.NONE
