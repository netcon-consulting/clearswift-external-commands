# check_string.py V4.0.0
#
# Copyright (c) 2020-2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "search_strings", )

def run_command(input, log, config, additional, optional):
    """
    Check raw email data for combination of strings.

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

    email = email.as_bytes()

    for list_string in config.search_strings:
        for string in list_string:
            if email.find(string.encode(CHARSET_UTF8)) == -1:
                break
        else:
            return ReturnCode.DETECTED

    return ReturnCode.NONE
