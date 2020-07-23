#!/usr/bin/env python3

# replace_url.py V1.0.0
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys
import re
from bs4 import BeautifulSoup

#########################################################################################

from netcon import ParserEmailLog, read_config, read_email, write_log, get_expression_list, html2text

DESCRIPTION = "replaces URLs in text and html body if one of the keywords in CS expression list is found"

class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0  - email not modified
    1  - one or more URL replaced
    99 - error
    255 - unhandled exception
    """
    NOT_MODIFIED = 0
    URL_REPLACED = 1
    ERROR = 99
    EXCEPTION = 255

PARSER = ParserEmailLog

CONFIG_PARAMETERS = ( "name_expression_list", "url_replacement" )

PATTERN_URL = re.compile(r"([\s<([{\"]|^)+((https?://|www\.|ftp\.)[^\s>)\]}\"]+)([\s>)\]}\"]|$)+", re.I)

def main(args):
    try:
        config = read_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.email)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    try:
        set_expression = get_expression_list(config.name_expression_list)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    if not set_expression:
        write_log(args.log, "Expression list is empty")

        return ReturnCode.ERROR

    part_text = None
    part_html = None

    for part in email.walk():
        if not part_text and part.get_content_type() == "text/plain":
            part_text = part
        elif not part_html and part.get_content_type() == "text/html":
            part_html = part

        if part_text and part_html:
            break

    list_pattern = list()

    for expression in set_expression:
        list_pattern.append(re.compile(expression, re.I))

    expression_found = False

    if part_text:
        content_text = part_text.get_payload(decode=True).decode("utf-8")

        for pattern in list_pattern:
            match = re.search(pattern, content_text)

            if match:
                expression_found = True

                break

    if part_html:
        content_html = part_html.get_payload(decode=True).decode("utf-8")

        if not expression_found:
            text_html = html2text(content_html)

            for pattern in list_pattern:
                match = re.search(pattern, text_html)

                if match:
                    expression_found = True

                    break

    if expression_found:
        if part_text:
            set_url = { url for (_, url, _, _) in re.findall(PATTERN_URL, content_text) }

            for url in set_url:
                content_text = content_text.replace(url, config.url_replacement)

            part_text.set_payload(content_text)

        if part_html:
            soup = BeautifulSoup(content_html, features="html5lib")

            for a in soup.findAll("a", href=True):
                a["href"] = config.url_replacement

            content_html = str(soup)

            part_html.set_payload(content_html)

        try:
            with open(args.email, "w") as f:
                f.write(email.as_string())
        except:
            write_log(args.log, "Error writing '{}'".format(args.email))

            return ReturnCode.ERROR

        return ReturnCode.URL_REPLACED

    return ReturnCode.NOT_MODIFIED

#########################################################################################

if __name__ == "__main__":
    if __file__.endswith(".py"):
        config_default = __file__[:-3] + ".toml"
    else:
        config_default = __file__ + ".toml"

    parser = PARSER(DESCRIPTION, config_default)

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
