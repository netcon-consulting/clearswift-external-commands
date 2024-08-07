# add_tag.py V8.1.1
#
# Copyright (c) 2021-2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from sys import setrecursionlimit
from re import compile, search, escape
from email.utils import parseaddr, getaddresses

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "address_tag", "internal_list", "subject_tag", "text_tag", "text_top", "html_tag", "html_top", "html_id", "calendar_tag" )

RECURSION_LIMIT = 5000

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Add tags in address and subject headers, text and HTML bodies and calendar objects.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    :type disable_splitting: bool
    :type reformat_header: bool
    """
    if not (config.address_tag or config.subject_tag or config.text_tag or config.html_tag or config.calendar_tag):
        return ReturnCode.NONE

    try:
        email = read_email(input, disable_splitting)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    setrecursionlimit(RECURSION_LIMIT)

    email_modified = False

    if config.address_tag:
        # add address tag

        for header_keyword in [ "From", "Sender" ]:
            if header_keyword in email:
                address_tag = f"{config.address_tag} "

                try:
                    (prefix, address) = parseaddr(email[header_keyword])
                except Exception:
                    write_log(log, f"Cannot parse {header_keyword} header")

                    return ReturnCode.DETECTED

                if address and not prefix.startswith(address_tag):
                    if prefix:
                        header = f'"{config.address_tag} {prefix}" <{address}>'
                    else:
                        header = f'"{config.address_tag} {address}" <{address}>'

                    del email[header_keyword]
                    email[header_keyword] = header

                    email_modified = True

        if config.internal_list:
            # add address tag to external addresses in To/Cc header

            try:
                set_domain = set(url_list(config.internal_list))
            except Exception as ex:
                write_log(log, ex)

                return ReturnCode.DETECTED

            pattern_domain = compile(r"^\S+@(\S+)")

            for header_keyword in [ "To", "Cc" ]:
                if header_keyword in email:
                    try:
                        list_address = getaddresses(email.get_all(header_keyword))
                    except Exception:
                        write_log(log, f"Cannot parse '{header_keyword}' header")

                        return ReturnCode.DETECTED

                    if list_address:
                        header = ""
                        header_modified = False

                        for (prefix, address) in list_address:
                            if address:
                                match = search(pattern_domain, address)

                                if match is not None and match.group(1).lower() not in set_domain and not prefix.startswith(address_tag):
                                    if prefix:
                                        prefix = f"{config.address_tag} {prefix}"
                                    else:
                                        prefix = f"{config.address_tag} {address}"

                                    header_modified = True

                                header += f'"{prefix}" <{address}>, '

                        if header_modified:
                            del email[header_keyword]
                            email[header_keyword] = header[:-2]

                            email_modified = True

    if config.subject_tag and "Subject" in email:
        # add subject tag

        header = email["Subject"].strip()

        if not header.startswith(f"{config.subject_tag} "):
            del email["Subject"]
            email["Subject"] = f"{config.subject_tag} {header}"

            email_modified = True

    if config.text_tag:
        # add text body tag

        try:
            part = extract_part(email, TYPE_TEXT)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        if part is not None:
            (part, charset, content) = part

            annotation_content = annotation(config.text_tag).text

            if config.text_top:
                content = annotation_content + content
            else:
                content += annotation_content

            if charset != CHARSET_UTF8 and not string_ascii(annotation_content):
                charset = CHARSET_UTF8

            if HEADER_CTE in part:
                del part[HEADER_CTE]

            part.set_payload(content, charset=charset)

            email_modified = True

    if config.html_tag:
        # add HTML body tag

        try:
            part = extract_part(email, TYPE_HTML)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        if part is not None:
            (part, charset, content) = part

            annotation_content = f'<div id="{config.html_id}">{annotation(config.html_tag).html}</div>'

            content = annotate_html(content, annotation_content)

            if charset != CHARSET_UTF8 and not string_ascii(annotation_content):
                charset = CHARSET_UTF8

            if HEADER_CTE in part:
                del part[HEADER_CTE]

            part.set_payload(content, charset=charset)

            email_modified = True

    if config.calendar_tag:
        # add calendar tag

        try:
            part = extract_part(email, TYPE_CALENDAR)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        if part is not None:
            (part, charset, content) = part

            match = search(r"(^|\n)(ORGANIZER;[\S\s\r\n]*?)(\r?\n\S|$)", content)

            if match is not None:
                organizer = match.group(2)
                organizer_start = match.start(2)

                match = search(r"[;:]CN=", organizer)

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
                    else:
                        name = search(r"[^:;]*", organizer[name_start:]).group(0)

                    if search(fr"^{escape(config.calendar_tag)} ", name) is None:
                        if HEADER_CTE in part:
                            del part[HEADER_CTE]

                        if charset != CHARSET_UTF8 and not string_ascii(config.calendar_tag):
                            charset = CHARSET_UTF8

                        part.set_payload(content[:organizer_start + name_start] + config.calendar_tag + " " + content[organizer_start + name_start:], charset=charset)

                        email_modified = True

    if email_modified:
        try:
            write_email(email, input, reformat_header)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        return ReturnCode.MODIFIED

    return ReturnCode.NONE
