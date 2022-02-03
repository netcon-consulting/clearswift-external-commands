# check_qr.py V3.1.0
#
# Copyright (c) 2021-2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
from PIL import Image
from pyzbar.pyzbar import decode

ADDITIONAL_ARGUMENTS = ( )
CONFIG_PARAMETERS = ( "url_blacklist", "url_whitelist" )

def run_command(input, log, config, additional):
    """
    Check URLs from QR-codes in pictures against URL blacklist and corresponding domains against reputation blacklists.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    """
    try:
        image = Image.open(input)
    except Exception:
        write_log(log, "Cannot read image '{}'".format(input))

        return ReturnCode.ERROR

    list_qr = decode(image)

    if list_qr:
        set_url = set()

        for qr_code in list_qr:
            try:
                set_url |= set(re.finditer(PATTERN_URL, qr_code.data.decode(CHARSET_UTF8)))
            except Exception:
                pass

        if set_url:
            if config.url_blacklist:
                try:
                    set_blacklist = set(url_list(config.url_blacklist))
                except Exception as ex:
                    write_log(log, ex)

                    return ReturnCode.ERROR

                set_blacklist = { re.compile(url2regex(url), re.IGNORECASE) for url in set_blacklist }
            else:
                set_blacklist = None

            if config.url_whitelist:
                try:
                    set_whitelist = set(url_list(config.url_whitelist))
                except Exception as ex:
                    write_log(log, ex)

                    return ReturnCode.ERROR

                set_whitelist = { re.compile(url2regex(url), re.IGNORECASE) for url in set_whitelist }
            else:
                set_whitelist = None

            set_clean = set()

            for url in set_url:
                if url not in set_clean:
                    result = url_blacklisted(url, set_whitelist, set_blacklist)

                    if result is not None:
                        if result:
                            write_log(log, "'{}' listed on '{}'".format(result[0], result[1]))

                        write_log(log, "'{}' listed on '{}'".format(url, config.url_blacklist))

                        return ReturnCode.DETECTED

                    set_clean.add(url)

    return ReturnCode.NONE
