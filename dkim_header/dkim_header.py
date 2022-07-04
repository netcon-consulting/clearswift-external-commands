# dkim_header.py V6.0.0
#
# Copyright (c) 2021-2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re

ADDITIONAL_ARGUMENTS = ( "spamlogic", )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( )

HEADER_DKIM = "x-dkim-check"

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Add header with result of SpamLogic DKIM check.

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

        return ReturnCode.DETECTED

    match = re.search(r';\s?dkim="([^"]+)";', additional.spamlogic)

    if match is None:
        write_log(log, "Cannot extract DKIM check result from SpamLogic info")

        return ReturnCode.DETECTED

    del email[HEADER_DKIM]

    email[HEADER_DKIM] = match.group(1)

    try:
        write_email(email, input, reformat_header)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    return ReturnCode.MODIFIED
