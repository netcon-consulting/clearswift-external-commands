#!/usr/bin/env python3

# check_custom.py V1.0.0
#
# Copyright (c) 2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

from netcon import ParserArgs, get_config, read_email, write_log

DESCRIPTION = "check email with configurable custom function"

@enum.unique
class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0   - not detected
    1   - detected
    99  - error
    255 - unhandled exception
    """
    NOT_DETECTED = 0
    DETECTED = 1
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "check_function", )

CODE_SKIPPED = ReturnCode.NOT_DETECTED

def main(args):
    try:
        config = get_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    try:
        exec(config.check_function)

        return check_email(email, args.log)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

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
