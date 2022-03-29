# check_rcptlimit.py V4.0.0
#
# Copyright (c) 2020-2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "recipient_limit", )

def run_command(input, log, config, additional, optional):
    """
    Check number of recipients (in To and Cc headers) against limit.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    """
    try:
        email = read_email(input)
    except Exception as ex:
        write_log(log, ex)

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
        return ReturnCode.DETECTED

    return ReturnCode.NONE
