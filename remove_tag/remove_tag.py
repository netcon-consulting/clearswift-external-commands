# remove_tag.py V7.0.1
#
# Copyright (c) 2021-2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
from email.utils import getaddresses
from bs4 import BeautifulSoup

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "address_tag", "clean_text", "clean_html", "subject_tag", "text_tag", "html_id", "calendar_tag" )

RECURSION_LIMIT = 5000

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Remove tags in address and subject headers, text and HTML bodies and calendar objects.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    :type disable_splitting: bool
    :type reformat_header: bool
    """
    if not (config.address_tag or config.subject_tag or config.text_tag or config.html_id or config.calendar_tag):
        return ReturnCode.NONE

    try:
        email = read_email(input, disable_splitting)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    sys.setrecursionlimit(RECURSION_LIMIT)

    email_modified = False

    if config.address_tag:
        # remove address tag

        address_tag = "{} ".format(config.address_tag)

        length_tag = len(address_tag)

        for header_keyword in [ "To", "Cc" ]:
            if header_keyword in email:
                try:
                    list_address = getaddresses(email.get_all(header_keyword))
                except Exception:
                    write_log(log, "Cannot parse {} header".format(header_keyword))

                    return ReturnCode.DETECTED

                if list_address:
                    header = ""
                    header_modified = False

                    for (prefix, address) in list_address:
                        if address:
                            if prefix.startswith(address_tag):
                                prefix = prefix[length_tag:]

                                header_modified = True

                            header += '"{}" <{}>, '.format(prefix, address)

                    if header_modified:
                        del email[header_keyword]
                        email[header_keyword] = header[:-2]

                        email_modified = True

    if config.subject_tag and "Subject" in email:
        # remove subject tag

        header = email.get("Subject").strip()

        match = re.search(r"{} ".format(re.escape(config.subject_tag)), header)

        if match is not None:
            del email["Subject"]
            email["Subject"] = header[:match.start()] + header[match.end():]

            email_modified = True

    if (config.text_tag or (config.address_tag and config.clean_text)):
        # remove text body tag and address tag from text body

        try:
            part = extract_part(email, TYPE_TEXT)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        if part is not None:
            (part, charset, content) = part

            body_modified = False

            if config.text_tag:
                split_tag = annotation(config.text_tag).text.split("\n")

                while not split_tag[-1]:
                    del split_tag[-1]

                pattern_tag = re.compile("\\n".join([ r"(>+ )*" + re.escape(item) for item in split_tag ]) + r"\n")

                match = re.search(pattern_tag, content)

                if match is not None:
                    content = re.sub(pattern_tag, "", content)

                    body_modified = True

            if config.address_tag and config.clean_text and address_tag in content:
                content = content.replace(address_tag, "")

                body_modified = True

            if body_modified:
                if HEADER_CTE in part:
                    del part[HEADER_CTE]

                part.set_payload(content, charset=charset)

                email_modified = True

    if (config.html_id or (config.address_tag and config.clean_html)):
        # remove HTML body tag and address tag from HTML body

        try:
            part = extract_part(email, TYPE_HTML)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        if part is not None:
            (part, charset, content) = part

            body_modified = False

            soup = BeautifulSoup(content, features="html5lib")

            list_tag = soup.find_all("div", id=re.compile(r".*{}.*".format(re.escape(config.html_id))))

            if list_tag:
                for tag in list_tag:
                    tag.decompose()

                try:
                    content = soup.encode(charset).decode(charset)
                except Exception:
                    write_log(log, "Error converting soup to string")

                    return ReturnCode.DETECTED

                body_modified = True

            if config.address_tag and config.clean_html and address_tag in content:
                content = content.replace(address_tag, "")

                body_modified = True

            if body_modified:
                if HEADER_CTE in part:
                    del part[HEADER_CTE]

                part.set_payload(content, charset=charset)

                email_modified = True

    if config.calendar_tag:
        # remove calendar tag

        try:
            part = extract_part(email, TYPE_CALENDAR)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        if part is not None:
            (part, charset, content) = part

            match = re.search(r"(^|\n)(ORGANIZER;[\S\s\r\n]*?)(\r?\n\S|$)", content)

            if match is not None:
                organizer = match.group(2)
                organizer_start = match.start(2)

                match = re.search(r"[;:]CN=", organizer)

                if match is not None:
                    name_start = match.start() + 4

                    if organizer[name_start] == '"':
                        name_start += 1

                        name = ""

                        for (index, char) in enumerate(organizer[name_start:]):
                            if char == '"':
                                if end_escape(organizer[name_start:name_start + index]):
                                    name += char
                                else:
                                    break
                            else:
                                name += char

                        name_end = name_start + index - 1
                    else:
                        match = re.search(r"[^:;]*", organizer[name_start:])

                        name = match.group(0)
                        name_end = name_start + match.end(0)

                    match = re.search(r"^{} ".format(re.escape(config.calendar_tag)), name)

                    if match is not None:
                        if HEADER_CTE in part:
                            del part[HEADER_CTE]

                        if charset != CHARSET_UTF8 and not string_ascii(config.calendar_tag):
                            charset = CHARSET_UTF8

                        part.set_payload(content[:organizer_start + name_start] + name[match.end():] + content[organizer_start + name_end:], charset=charset)

                        email_modified = True

    if email_modified:
        try:
            write_email(email, input, reformat_header)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        return ReturnCode.MODIFIED

    return ReturnCode.NONE
