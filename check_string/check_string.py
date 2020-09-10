#!/usr/bin/env python3

# check_string.py V1.2.1
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

from netcon import ParserArgs, read_config, read_email, write_log

DESCRIPTION = "checks raw email text for combination of strings"

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

def main(args):
    try:
        config = read_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    email = email.as_string()

    for list_string in config.search_strings:
        for string in list_string:
            if email.find(string) == -1:
                break
        else:
            return ReturnCode.STRING_FOUND

    return ReturnCode.NOT_FOUND

#########################################################################################

if __name__ == "__main__":
    if CONFIG_PARAMETERS:
        if __file__.endswith(".py"):
            config_default = __file__[:-3] + ".toml"
        else:
            config_default = __file__ + ".toml"

        parser = ParserArgs(DESCRIPTION, config_default=config_default)
    else:
        parser = ParserArgs(DESCRIPTION)

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
