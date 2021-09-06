#!/usr/bin/env python3

# dkim_header.py V1.0.0
#
# Copyright (c) 2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import re
from netcon import ParserArgs, read_email, write_log

DESCRIPTION = "add header with result of SpamLogic DKIM check"

@enum.unique
class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0   - email not modified
    1   - header added
    99  - error
    255 - unhandled exception
    """
    NOT_MODIFIED = 0
    HEADER_ADDED = 1
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( )

CODE_SKIPPED = ReturnCode.NOT_MODIFIED

HEADER_DKIM = "x-dkim-check"

def main(args):
    try:
        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    match = re.search(r';\\idkim="([^"]+)";', args.spamlogic)

    if match is None:
        write_log(args.log, "Cannot extract DKIM check result from SpamLogic info")

        return ReturnCode.ERROR

    del email[HEADER_DKIM]

    email[HEADER_DKIM] = match.group(1)

    try:
        with open(args.input, "wb") as f:
            f.write(email.as_bytes())
    except Exception:
        write_log(args.log, "Error writing '{}'".format(args.input))

        return ReturnCode.ERROR

    return ReturnCode.HEADER_ADDED

#########################################################################################

if __name__ == "__main__":
    parser = ParserArgs(DESCRIPTION, bool(CONFIG_PARAMETERS), CODE_SKIPPED is not None)

    parser.add_argument("spamlogic", metavar="SPAMLOGIC", type=str, help="SpamLogic info")

    args = parser.parse_args()

    if CODE_SKIPPED is not None and args.type != "Message":
        # skip embedded/attached SMTP messages
        sys.exit(CODE_SKIPPED)

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
