# replace_url.py V7.0.0
#
# Copyright (c) 2020-2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
from bs4 import BeautifulSoup

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "keyword_list", "url_replacement" )

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Replace URLs in text and html body if one of the keywords is found.

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

    try:
        set_keyword = set(lexical_list(config.keyword_list))
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    if not set_keyword:
        write_log(log, "keyword list is empty")

        return ReturnCode.DETECTED

    part_text = None
    part_html = None

    for part in email.walk():
        if part_text is None and part.get_content_type() == "text/plain":
            part_text = part
        elif part_html is None and part.get_content_type() == "text/html":
            part_html = part

        if part_text is not None and part_html is not None:
            break

    set_pattern = { re.compile(keyword, re.IGNORECASE) for keyword in set_keyword }

    keyword_found = False

    if part_text is not None:
        content_text = part_text.get_payload(decode=True).decode("utf-8", errors="ignore")

        for pattern in set_pattern:
            match = re.search(pattern, content_text)

            if match:
                keyword_found = True

                break

    if part_html is not None:
        content_html = part_html.get_payload(decode=True).decode("utf-8", errors="ignore")

        if not keyword_found:
            text_html = html2text(content_html)

            for pattern in set_pattern:
                match = re.search(pattern, text_html)

                if match:
                    keyword_found = True

                    break

    if keyword_found:
        if part_text is not None:
            for url in re.findall(PATTERN_URL, content_text):
                content_text = content_text.replace(url, config.url_replacement)

            part_text.set_payload(content_text)

        if part_html is not None:
            soup = BeautifulSoup(content_html, features="html5lib")

            for a in soup.findAll("a", href=True):
                a["href"] = config.url_replacement

            content_html = str(soup)

            part_html.set_payload(content_html)

        try:
            write_email(email, input, reformat_header)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        return ReturnCode.MODIFIED

    return ReturnCode.NONE
