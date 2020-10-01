#!/usr/bin/env python3

# check_private.py V1.0.1
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

from netcon import ParserArgs, read_config, read_email, write_log

DESCRIPTION = "checks sensitivity header for private keyword and that private mails not exceed max_size and have no attachments"

class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0   - private mail
    1   - not private mail
    2   - invalid private mail (size > max_size or has attachments)
    99  - error
    255 - unhandled exception
    """
    PRIVATE = 0
    NOT_PRIVATE = 1
    INVALID = 2
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "max_size_kb", )

def main(args):
    try:
        config = read_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    if "Sensitivity" in email and str(email.get("Sensitivity")) == "private":
        if len(email.as_string()) > config.max_size_kb * 1024:
            write_log(args.log, "Mail exceeds max size")

            return ReturnCode.INVALID

        for part in email.walk():
            content_disposition = part.get_params(header="Content-Disposition")

            if content_disposition:
                for (key, _) in content_disposition:
                    if key == "attachment":
                        write_log(args.log, "Mail has attachment")

                        return ReturnCode.INVALID

        return ReturnCode.PRIVATE

    return ReturnCode.NOT_PRIVATE

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
