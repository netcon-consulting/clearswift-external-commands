#!/usr/bin/env python3

# check_private.py V2.1.1
#
# Copyright (c) 2020-2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

from netcon import ParserArgs, get_config, read_email, write_log

DESCRIPTION = "check sensitivity header for private keyword and that private mails not exceed size limit and have no attachments"

@enum.unique
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

CODE_SKIPPED = ReturnCode.PRIVATE

def main(args):
    try:
        config = get_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    if "Sensitivity" in email and str(email.get("Sensitivity")) == "private":
        if len(email.as_bytes()) > config.max_size_kb * 1024:
            write_log(args.log, "Mail exceeds max size")

            return ReturnCode.INVALID

        for part in email.walk():
            if part.is_attachment():
                write_log(args.log, "Mail has attachment")

                return ReturnCode.INVALID

        return ReturnCode.PRIVATE

    return ReturnCode.NOT_PRIVATE

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
