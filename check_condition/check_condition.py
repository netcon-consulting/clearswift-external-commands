# check_condition.py V1.1.0
#
# Copyright (c) 2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from re import search

ADDITIONAL_ARGUMENTS = ( "client_ip", "client_hostname", "sender" )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "condition_check", )

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Check custom condition.

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

    match = search(r"S:<?([^>]*)>?", additional.sender)

    if match is None:
        write_log(log, "Invalid sender")

        return ReturnCode.ERROR
    else:
        sender = match.group(1)

    try:
        condition_check = lexical_list(config.condition_check).pop()
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    if not condition_check:
        write_log(log, "Condition check is empty")

        return ReturnCode.ERROR

    try:
        exec(condition_check, globals())
    except Exception:
        write_log(args.log, "Cannot load condition check")

        return ReturnCode.ERROR

    try:
        if check_condition(additional.client_ip, additional.client_hostname, sender, email):
            return ReturnCode.DETECTED
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    return ReturnCode.NONE
