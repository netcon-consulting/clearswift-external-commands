# remove_tag.py V1.0.0
#
# Copyright (c) 2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
import bs4

ADDITIONAL_ARGUMENTS = ( )
CONFIG_PARAMETERS = ( "address_tag", "name_domain_list", "clean_text", "clean_html", "subject_tag", "text_tag", "text_top", "html_tag", "html_top", "html_tag_id", "calendar_tag" )

RECURSION_LIMIT = 5000

def run_command(input, log, config, additional):
    """
    Remove tags in address and subject headers, text and html bodies and calendar objects.

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

    sys.setrecursionlimit(RECURSION_LIMIT)

    email_modified = False

    if config.address_tag:
        # remove address tag

        string_tag = "{} ".format(config.address_tag)

        pattern_tag = re.compile(r'^"?{} '.format(re.escape(config.address_tag)))

        for header_keyword in [ "To", "Cc" ]:
            if header_keyword in email:
                list_address = extract_addresses(", ".join(email.get_all(header_keyword)))

                if list_address:
                    header = ""
                    header_modified = False

                    for (prefix, address, suffix) in list_address:
                        if prefix.startswith(";") or prefix.startswith(","):
                            prefix = prefix[1:]

                        if prefix.endswith("<") and suffix.startswith(">"):
                            prefix = prefix[:-1]
                            suffix = suffix[1:]

                        prefix = prefix.strip()
                        suffix = suffix.strip()

                        if re.search(pattern_tag, prefix):
                            if prefix.startswith('"'):
                                prefix = '"' + prefix[len(config.address_tag) + 2:]
                            else:
                                prefix = prefix[len(config.address_tag) + 1:]

                            header_modified = True

                        if prefix:
                            header += prefix + " "

                        header += "<" + address + ">"

                        if suffix:
                            header += " " + suffix

                        header += ", "

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
            part = extract_part(email, "text/plain")
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.INVALID_ENCODING

        if part is not None:
            (part, charset, content) = part

            body_modified = False

            if config.text_tag:
                split_tag = config.text_tag.split("\n")

                while not split_tag[-1]:
                    del split_tag[-1]

                pattern_tag = re.compile("\\n".join([ r"(>+ )*" + re.escape(item) for item in split_tag ]) + r"\n")

                match = re.search(pattern_tag, content)

                if match is not None:
                    content = re.sub(pattern_tag, "", content)

                    body_modified = True

            if config.address_tag and config.clean_text and string_tag in content:
                content = content.replace(string_tag, "")

                body_modified = True

            if body_modified:
                if HEADER_CTE in part:
                    del part[HEADER_CTE]

                part.set_payload(content, charset=charset)

                email_modified = True

    if (config.html_tag or (config.address_tag and config.clean_html)):
        # remove html body tag and address tag from html body

        try:
            part = extract_part(email, "text/html")
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.INVALID_ENCODING

        if part is not None:
            (part, charset, content) = part

            body_modified = False

            soup = bs4.BeautifulSoup(content, features="html5lib")

            list_tag = soup.find_all("div", id=re.compile(r".*{}.*".format(re.escape(config.html_tag_id))))

            if list_tag:
                for tag in list_tag:
                    tag.decompose()

                try:
                    content = soup.encode(charset).decode(charset)
                except Exception:
                    write_log(log, "Error converting soup to string")

                    return ReturnCode.ERROR

                body_modified = True

            if config.address_tag and config.clean_html and string_tag in content:
                content = content.replace(string_tag, "")

                body_modified = True

            if body_modified:
                if HEADER_CTE in part:
                    del part[HEADER_CTE]

                part.set_payload(content, charset=charset)

                email_modified = True

    if config.calendar_tag:
        # remove calendar tag

        try:
            part = extract_part(email, "text/calendar")
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.INVALID_ENCODING

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
            with open(input, "wb") as f:
                f.write(email.as_bytes())
        except Exception:
            write_log(log, "Error writing '{}'".format(input))

            return ReturnCode.ERROR

        return ReturnCode.MODIFIED

    return ReturnCode.NONE
