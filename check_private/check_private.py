# check_private.py V5.0.0
#
# Copyright (c) 2020-2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "max_size", )

def run_command(input, log, config, additional, optional):
    """
    Check sensitivity header for private keyword and that private mails not exceed size limit and have no attachments.

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

    if "Sensitivity" in email and str(email.get("Sensitivity")) == "private":
        if len(email.as_bytes()) > config.max_size * 1024:
            write_log(log, "Mail exceeds max size")

            return ReturnCode.MODIFIED

        for part in email.walk():
            if part.is_attachment():
                write_log(log, "Mail has attachment")

                return ReturnCode.MODIFIED

        return ReturnCode.NONE

    return ReturnCode.DETECTED
