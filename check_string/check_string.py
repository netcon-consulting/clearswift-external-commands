#!/usr/bin/env python3

# check_string.py V2.1.1
#
# Copyright (c) 2020-2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

from netcon import ParserArgs, get_config, read_email, write_log, CHARSET_UTF8

DESCRIPTION = "check raw email data for combination of strings"

@enum.unique
class ReturnCode(enum.IntEnum):
    """
    Return code.

    0   - no string combination found
    1   - string combination found
    99  - error
    255 - unhandled exception
    """
    NOT_FOUND = 0
    STRING_FOUND = 1
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "search_strings", )

CODE_SKIPPED = ReturnCode.NOT_FOUND

def main(args):
    try:
        config = get_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    email = email.as_bytes()

    for list_string in config.search_strings:
        for string in list_string:
            if email.find(string.encode(CHARSET_UTF8)) == -1:
                break
        else:
            return ReturnCode.STRING_FOUND

    return ReturnCode.NOT_FOUND

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
