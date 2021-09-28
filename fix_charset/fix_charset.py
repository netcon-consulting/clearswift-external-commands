# fix_charset.py V3.0.0
#
# Copyright (c) 2020-2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re

ADDITIONAL_ARGUMENTS = ( )
CONFIG_PARAMETERS = ( )

def run_command(input, log, config, additional):
    """
    Set charset in meta tag in html body to charset defined in content-type header.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    """
    HEADER_CTE = "Content-Transfer-Encoding"

    try:
        email = read_email(input)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    for part in email.walk():
        if part.get_content_type() == "text/html":
            charset_mime = part.get_content_charset()

            if charset_mime:
                content = part.get_payload(decode=True).decode(charset_mime, errors="ignore")

                match = re.search(r"<meta [^>]*charset=\"?([^;\"> ]+)", content, flags=re.IGNORECASE)

                if match is not None:
                    charset_meta = match.group(1).lower()

                    if charset_mime != charset_meta:
                        content = re.sub(r"(<meta [^>]*charset=\"?)({})".format(charset_meta), r"\1{}".format(charset_mime), content, flags=re.IGNORECASE)

                        if HEADER_CTE in part:
                            del part[HEADER_CTE]

                        part.set_payload(content, charset=charset_mime)

                        try:
                            with open(input, "wb") as f:
                                f.write(email.as_bytes())
                        except Exception:
                            write_log(log, "Error writing '{}'".format(input))

                            return ReturnCode.ERROR

                        return ReturnCode.MODIFIED

    return ReturnCode.NONE
