# check_qr.py V2.0.0
#
# Copyright (c) 2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
from PIL import Image
from pyzbar.pyzbar import decode

ADDITIONAL_ARGUMENTS = ( )
CONFIG_PARAMETERS = ( "name_url_blacklist", "name_url_whitelist" )

def run_command(input, log, config, additional):
    """
    Check URLs from QR-codes in pictures against URL blacklist and corresponding domains against reputation blacklists.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    """
    PATTERN_URL = re.compile(r"(https?://|www\.|ftp\.)\S+", re.IGNORECASE)
    PATTERN_DOMAIN = re.compile(r"^(https?://)?([^/]+)\S*$", re.IGNORECASE)

    try:
        image = Image.open(input)
    except Exception:
        write_log(log, "Cannot read image '{}'".format(input))

        return ReturnCode.ERROR

    list_qr = decode(image)

    for qr_code in list_qr:
        try:
            text = qr_code.data.decode(CHARSET_UTF8)
        except Exception:
            text = None

        if text is not None and re.search(PATTERN_URL, text) is not None:
            try:
                set_url = get_url_list(config.name_url_blacklist)
            except Exception as ex:
                write_log(log, ex)

                return ReturnCode.ERROR

            set_blacklist = { re.compile(url2regex(url), re.IGNORECASE) for url in set_url }

            try:
                set_url = get_url_list(config.name_url_whitelist)
            except Exception as ex:
                write_log(log, ex)

                return ReturnCode.ERROR

            set_whitelist = { re.compile(url2regex(url), re.IGNORECASE) for url in set_url }

            for match in re.finditer(PATTERN_URL, text):
                url = match.group()

                for pattern in set_whitelist:
                    if re.search(pattern, url) is not None:
                        break
                else:
                    for pattern in set_blacklist:
                        if re.search(pattern, url) is not None:
                            write_log(log, "'{}' listed on '{}'".format(url, config.name_url_blacklist))

                            return ReturnCode.DETECTED

                    domain = re.search(PATTERN_DOMAIN, url).group(2).lower()

                    while True:
                        blacklist = domain_blacklisted(domain)

                        if blacklist is not None:
                            write_log(log, "'{}' listed on '{}'".format(domain, blacklist))

                            return ReturnCode.DETECTED

                        index = domain.find(".")

                        if index < 0:
                            break

                        domain = domain[index + 1:]

    return ReturnCode.NONE
