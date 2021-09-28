# replace_url.py V3.0.0
#
# Copyright (c) 2020-2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
from bs4 import BeautifulSoup

ADDITIONAL_ARGUMENTS = ( )
CONFIG_PARAMETERS = ( "name_expression_list", "url_replacement" )

PATTERN_URL = re.compile(r"([\s<([{\"]|^)+((https?://|www\.|ftp\.)[^\s>)\]}\"]+)([\s>)\]}\"]|$)+", re.IGNORECASE)

def run_command(input, log, config, additional):
    """
    Replace URLs in text and html body if one of the keywords is found.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    """
    try:
        email = read_email(input)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    try:
        set_expression = get_expression_list(config.name_expression_list)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    if not set_expression:
        write_log(log, "Expression list is empty")

        return ReturnCode.ERROR

    part_text = None
    part_html = None

    for part in email.walk():
        if part_text is None and part.get_content_type() == "text/plain":
            part_text = part
        elif part_html is None and part.get_content_type() == "text/html":
            part_html = part

        if part_text is not None and part_html is not None:
            break

    list_pattern = list()

    for expression in set_expression:
        list_pattern.append(re.compile(expression, re.IGNORECASE))

    expression_found = False

    if part_text is not None:
        content_text = part_text.get_payload(decode=True).decode("utf-8", errors="ignore")

        for pattern in list_pattern:
            match = re.search(pattern, content_text)

            if match:
                expression_found = True

                break

    if part_html is not None:
        content_html = part_html.get_payload(decode=True).decode("utf-8", errors="ignore")

        if not expression_found:
            text_html = html2text(content_html)

            for pattern in list_pattern:
                match = re.search(pattern, text_html)

                if match:
                    expression_found = True

                    break

    if expression_found:
        if part_text is not None:
            set_url = { url for (_, url, _, _) in re.findall(PATTERN_URL, content_text) }

            for url in set_url:
                content_text = content_text.replace(url, config.url_replacement)

            part_text.set_payload(content_text)

        if part_html is not None:
            soup = BeautifulSoup(content_html, features="html5lib")

            for a in soup.findAll("a", href=True):
                a["href"] = config.url_replacement

            content_html = str(soup)

            part_html.set_payload(content_html)

        try:
            with open(input, "wb") as f:
                f.write(email.as_bytes())
        except Exception:
            write_log(log, "Error writing '{}'".format(input))

            return ReturnCode.ERROR

        return ReturnCode.MODIFIED

    return ReturnCode.NONE
