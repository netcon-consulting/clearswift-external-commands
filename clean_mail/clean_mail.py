# clean_mail.py V1.0.1
#
# Copyright (c) 2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
from email.message import EmailMessage
from bs4 import BeautifulSoup

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "regex_list", "annotation_list", "clean_attachment" )

RECURSION_LIMIT = 5000

PATTERN_ID = re.compile(r"^<\S+[^>]*[ \t\n]+id=\"(\S+)\"[ \t\n>]")

def clean_mail(email, list_pattern, list_annotation):
    """
    Clean patterns and annotations from email.

    :type email: EmailMessage
    :type list_pattern: list
    :type list_annotation: list
    :rtype: bool
    """
    email_modified = False

    # clean text body
    part = extract_part(email, "text/plain")

    if part is not None:
        (part, charset, content) = part

        body_modified = False

        if list_annotation is not None:
            for annotation in list_annotation:
                split_annotation = annotation.text.split("\n")

                while not split_annotation[-1]:
                    del split_annotation[-1]

                pattern_annotation = re.compile("\\n".join([ r"(>+ )*" + re.escape(item) for item in split_annotation ]) + r"\n")

                match = re.search(pattern_annotation, content)

                if match is not None:
                    content = re.sub(pattern_annotation, "", content)

                    body_modified = True

        if list_pattern is not None:
            for pattern in list_pattern:
                match = re.search(pattern, content)

                if match is not None:
                    content = re.sub(pattern, "", content)

                    body_modified = True

        if body_modified:
            if HEADER_CTE in part:
                del part[HEADER_CTE]

            part.set_payload(content, charset=charset)

            email_modified = True

    # clean HTML body
    part = extract_part(email, "text/html")

    if part is not None:
        (part, charset, content) = part

        body_modified = False

        soup = BeautifulSoup(content, features="html5lib")

        for annotation in list_annotation:
            match = re.search(PATTERN_ID, annotation.html.strip())

            if match is not None:
                list_tag = soup.find_all("div", id=re.compile(r".*{}.*".format(re.escape(match.group(1)))))

                if list_tag:
                    for tag in list_tag:
                        tag.decompose()

                    body_modified = True

        if list_pattern is not None:
            for pattern in list_pattern:
                for string in soup.findAll(text=pattern):
                    text = string.text

                    index_shift = 0

                    for match in re.finditer(pattern, text):
                        text = text[:match.start() + index_shift] + text[match.end() + index_shift:]

                        index_shift -= match.end() - match.start()

                    body_modified = True

                    string.replace_with(text)

        if body_modified:
            try:
                content = soup.encode(charset).decode(charset)
            except Exception:
                raise Exception("Error converting soup to string")

            if HEADER_CTE in part:
                del part[HEADER_CTE]

            part.set_payload(content, charset=charset)

            email_modified = True

    return email_modified

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Clean regular expressions and annotations from text and HTML mail bodies.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    :type disable_splitting: bool
    :type reformat_header: bool
    """
    if not (config.regex_list or config.annotation_list):
        return ReturnCode.NONE

    try:
        email = read_email(input, disable_splitting)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    sys.setrecursionlimit(RECURSION_LIMIT)

    if config.regex_list:
        try:
            list_pattern = [ re.compile(regex) for regex in lexical_list(config.regex_list) ]
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED
    else:
        list_pattern = None

    if config.annotation_list:
        try:
            list_annotation = [ annotation(name) for name in lexical_list(config.annotation_list) ]
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED
    else:
        list_annotation = None

    try:
        email_modified = clean_mail(email, list_pattern, list_annotation)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    if config.clean_attachment:
        for part in email.walk():
            if part.is_attachment() and part.get_content_type() == "message/rfc822":
                attached_email = part.get_payload()[0]

                if isinstance(attached_email, EmailMessage):
                    try:
                        email_modified |= clean_mail(attached_email, list_pattern, list_annotation)
                    except Exception as ex:
                        write_log(log, ex)

                        return ReturnCode.DETECTED

    if email_modified:
        try:
            write_email(email, input, reformat_header)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        return ReturnCode.MODIFIED

    return ReturnCode.NONE
