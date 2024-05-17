# check_rcptlimit.py V6.1.1
#
# Copyright (c) 2020-2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from email.utils import getaddresses

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "recipient_limit", )

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Check number of recipients (in To and Cc headers) against limit.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    :type disable_splitting: bool
    :type reformat_header: bool
    """
    try:
        email = read_email(input, disable_splitting)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    try:
        list_address = getaddresses(email.get_all("To") + email.get_all("Cc"))
    except Exception:
        write_log(log, "Cannot parse To/Cc header")

        return ReturnCode.ERROR

    if len(list_address) > config.recipient_limit:
        return ReturnCode.DETECTED

    return ReturnCode.NONE
