#!/usr/bin/env python3

# fix_charset.py V1.1.0
#
# Copyright (c) 2020-2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import re
from email.encoders import encode_quopri, encode_base64
from netcon import ParserArgs, read_email, write_log

DESCRIPTION = "sets charset in meta tag in html body to charset defined in content-type header"

@enum.unique
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

CONFIG_PARAMETERS = ( )

HEADER_CTE = "Content-Transfer-Encoding"

def main(args):
    try:
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

                        if HEADER_CTE in part:
                            cte = part.get(HEADER_CTE).lower()

                            if (cte == "quoted-printable"):
                                del part[HEADER_CTE]

                                encode_quopri(part)
                            elif (cte == "base64"):
                                del part[HEADER_CTE]

                                encode_base64(part)

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
    if CONFIG_PARAMETERS:
        parser = ParserArgs(DESCRIPTION, config=True)
    else:
        parser = ParserArgs(DESCRIPTION)

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
