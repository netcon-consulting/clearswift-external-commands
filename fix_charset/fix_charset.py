#!/usr/bin/env python3

# fix_charset.py V1.0.0
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import argparse
import re
from netcon import read_config, read_email, write_log

DESCRIPTION = "sets charset in meta tag in HMTL body to charset defined in Content-Type header"

class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0   - email not modified
    1   - charset changed
    99  - error
    255 - unhandled exception
    """
    NOT_MODIFIED = 0
    CHARSET_CHANGED = 1
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = (  )

def main(args):
    try:
        config = read_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    for part in email.walk():
        if part.get_content_type() == "text/html":
            charset_mime = part.get_content_charset()

            if charset_mime is not None:
                content = part.get_payload(decode=True).decode(charset_mime, errors="ignore")

                match = re.search(r'<meta [^>]*charset=([^;"> ]+)', content, re.I)

                if match:
                    charset_meta = match.group(1).lower()

                    if (charset_meta != charset_mime):
                        content = re.sub(r"(<meta [^>]*charset=)({})".format(charset_meta), r"\1{}".format(charset_mime), content, re.I)

                        part.set_payload(content.encode(charset_mime))

                        try:
                            with open(args.input, "wb") as f:
                                f.write(email.as_bytes())
                        except:
                            write_log(args.log, "Error writing '{}'".format(args.input))

                            return ReturnCode.ERROR

                        return ReturnCode.CHARSET_CHANGED

    return ReturnCode.NOT_MODIFIED

#########################################################################################

if __name__ == "__main__":
    if __file__.endswith(".py"):
        config_default = __file__[:-3] + ".toml"
    else:
        config_default = __file__ + ".toml"

    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        "-c",
        "--config",
        metavar="CONFIG",
        type=str,
        default=config_default,
        help="path to configuration file (default={})".format(config_default))
    parser.add_argument("input", metavar="INPUT", type=str, help="input file")
    parser.add_argument("log", metavar="LOG", type=str, help="log file")

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
