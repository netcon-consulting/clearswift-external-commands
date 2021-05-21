#!/usr/bin/env python3

# fix_charset.py V2.1.0
#
# Copyright (c) 2020-2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import re
from email.encoders import encode_quopri, encode_base64
from netcon import ParserArgs, read_email, write_log

DESCRIPTION = "set charset in meta tag in html body to charset defined in content-type header"

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

CODE_SKIPPED = ReturnCode.NOT_MODIFIED

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

            if charset_mime:
                content = part.get_payload(decode=True).decode(charset_mime, errors="ignore")

                match = re.search(r"<meta [^>]*charset=\"?([^;\"> ]+)", content, flags=re.IGNORECASE)

                if match is not None:
                    charset_meta = match.group(1).lower()

                    if charset_mime != charset_meta:
                        content = re.sub(r"(<meta [^>]*charset=\"?)({})".format(charset_meta), r"\1{}".format(charset_mime), content, flags=re.IGNORECASE)

                        if HEADER_CTE in part:
                            del part[HEADER_CTE]

                        part.set_payload(content, charset=charset_mime)

                        try:
                            with open(args.input, "wb") as f:
                                f.write(email.as_bytes())
                        except Exception:
                            write_log(args.log, "Error writing '{}'".format(args.input))

                            return ReturnCode.ERROR

                        return ReturnCode.CHARSET_CHANGED

    return ReturnCode.NOT_MODIFIED

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
