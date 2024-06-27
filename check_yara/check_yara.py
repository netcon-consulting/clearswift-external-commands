# check_yara.py V1.1.0
#
# Copyright (c) 2023-2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from yara import compile

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "yara_rules", )

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Check raw email data (or attachments) against YARA rules.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    :type disable_splitting: bool
    :type reformat_header: bool
    """
    try:
        data = read_binary(input)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    try:
        list_rules = lexical_list(config.yara_rules)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    try:
        rules = compile(source="\n".join(sorted(set(list_rules))))
    except Exception:
        write_log(log, "Invalid YARA rules")

        return ReturnCode.ERROR

    try:
        matches = rules.match(data=data)
    except Exception:
        write_log(log, "Error scanning data")

        return ReturnCode.ERROR

    if matches:
        write_log(log, str(matches)[1:-1])

        return ReturnCode.DETECTED

    return ReturnCode.NONE
