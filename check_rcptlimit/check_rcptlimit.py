#!/usr/bin/env python3

# check_rcptlimit.py V1.3.0
#
# Copyright (c) 2020-2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

from netcon import ParserArgs, get_config, read_email, write_log, extract_email_addresses

DESCRIPTION = "checks number of recipients (in to and cc headers) against limit"

@enum.unique
class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0   - number of recipients within limit
    1   - number of recipients exceeds limit
    99  - error
    255 - unhandled exception
    """
    LIMIT_OK = 0
    LIMIT_EXCEEDED = 1
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "recipient_limit", )

def main(args):
    try:
        config = get_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    num_recipients = 0

    # count number of email addresses in To and Cc headers
    for header_keyword in [ "To", "Cc" ]:
        if header_keyword in email:
            for header in email.get_all(header_keyword):
                email_addresses = extract_email_addresses(str(header))

                if email_addresses:
                    num_recipients += len(email_addresses)

    if num_recipients > config.recipient_limit:
        return ReturnCode.LIMIT_EXCEEDED

    return ReturnCode.LIMIT_OK

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
