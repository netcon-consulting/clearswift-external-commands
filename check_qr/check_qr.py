#!/usr/bin/env python3

# check_qr.py V1.1.0
#
# Copyright (c) 2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import re
from PIL import Image
from pyzbar.pyzbar import decode
from netcon import ParserArgs, get_config, write_log, get_url_list, domain_blacklisted, url2regex, CHARSET_UTF8

DESCRIPTION = "check URLs from QR-codes in pictures against URL blacklist and corresponding domains against reputation blacklists"

@enum.unique
class ReturnCode(enum.IntEnum):
    """
    Return code.

    0   - no QR-code with URL or URLs not malicious
    1   - QR-code with malicious URL
    99  - error
    255 - unhandled exception
    """
    OK = 0
    MALICIOUS = 1
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "name_url_blacklist", "name_url_whitelist" )

CODE_SKIPPED = None

def main(args):
    PATTERN_URL = re.compile(r"(https?://|www\.|ftp\.)\S+", re.IGNORECASE)
    PATTERN_DOMAIN = re.compile(r"^(https?://)?([^/]+)\S*$", re.IGNORECASE)

    try:
        config = get_config(args.config, CONFIG_PARAMETERS)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    try:
        image = Image.open(args.input)
    except Exception:
        write_log(args.log, "Cannot read image '{}'".format(args.input))

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
                write_log(args.log, ex)

                return ReturnCode.ERROR

            set_blacklist = { re.compile(url2regex(url), re.IGNORECASE) for url in set_url }

            try:
                set_url = get_url_list(config.name_url_whitelist)
            except Exception as ex:
                write_log(args.log, ex)

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
                            write_log(args.log, "'{}' listed on '{}'".format(url, config.name_url_blacklist))

                            return ReturnCode.MALICIOUS

                    domain = re.search(PATTERN_DOMAIN, url).group(2).lower()

                    while True:
                        blacklist = domain_blacklisted(domain)

                        if blacklist is not None:
                            write_log(args.log, "'{}' listed on '{}'".format(domain, blacklist))

                            return ReturnCode.MALICIOUS

                        index = domain.find(".")

                        if index < 0:
                            break

                        domain = domain[index + 1:]

    return ReturnCode.OK

#########################################################################################

if __name__ == "__main__":
    parser = ParserArgs(DESCRIPTION, bool(CONFIG_PARAMETERS), CODE_SKIPPED is not None)

    args = parser.parse_args()

    if CODE_SKIPPED is not None and args.type != "Message":
        # skip embedded/attached SMTP messages
        sys.exit(CODE_SKIPPED)

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
