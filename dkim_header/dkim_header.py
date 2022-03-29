# dkim_header.py V4.0.0
#
# Copyright (c) 2021-2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re

ADDITIONAL_ARGUMENTS = ( "spamlogic", )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( )

HEADER_DKIM = "x-dkim-check"

def run_command(input, log, config, additional, optional):
    """
    Add header with result of SpamLogic DKIM check.

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

        return ReturnCode.DETECTED

    match = re.search(r';\s?dkim="([^"]+)";', additional.spamlogic)

    if match is None:
        write_log(log, "Cannot extract DKIM check result from SpamLogic info")

        return ReturnCode.DETECTED

    del email[HEADER_DKIM]

    email[HEADER_DKIM] = match.group(1)

    try:
        with open(input, "wb") as f:
            f.write(email.as_bytes())
    except Exception:
        write_log(log, "Error writing '{}'".format(input))

        return ReturnCode.DETECTED

    return ReturnCode.MODIFIED
