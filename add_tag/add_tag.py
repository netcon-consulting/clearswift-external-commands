# add_tag.py V1.0.0
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
    Add tags in address and subject headers, text and html bodies and calendar objects.

    :type input: str
    :type log: str
    :type config: TupleConfig
    """
    HEADER_CTE = "Content-Transfer-Encoding"

    try:
        email = read_email(input)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    sys.setrecursionlimit(RECURSION_LIMIT)

    email_modified = False

    if config.address_tag and "From" in email:
        # add address tag

        pattern_tag = re.compile(r'^"?{} '.format(re.escape(config.address_tag)))

        list_address = extract_addresses(email.get("From"))

        if list_address:
            (prefix, address, suffix) = list_address[0]

            if prefix.endswith("<") and suffix.startswith(">"):
                prefix = prefix[:-1]
                suffix = suffix[1:]

            prefix = prefix.strip()
            suffix = suffix.strip()

            if not re.search(pattern_tag, prefix):
                prefix_new = ""

                for (index, char) in enumerate(prefix):
                    if char == '"':
                        if end_escape(prefix[:index]):
                            prefix_new += char
                    else:
                        prefix_new += char

                if prefix_new:
                    prefix = '"{} {}"'.format(config.address_tag, prefix_new)
                else:
                    prefix = '"{} {}"'.format(config.address_tag, address)

                del email["From"]
                email["From"] = prefix + " <" + address + "> " + suffix

                email_modified = True

        if config.name_domain_list:
            # add address tag to external addresses in To/Cc header

            try:
                set_address = get_address_list(config.name_domain_list)
            except Exception as ex:
                write_log(log, ex)

                return ReturnCode.ERROR

            pattern_domain = re.compile(r"^\S+@(\S+)")

            set_domain = { match.group(1).lower() for match in [ re.search(pattern_domain, address) for address in set_address ] if match is not None }

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

                            match = re.search(pattern_domain, address)

                            if match and match.group(1).lower() not in set_domain and not re.search(pattern_tag, prefix):
                                prefix_new = ""

                                for (index, char) in enumerate(prefix):
                                    if char == '"':
                                        if end_escape(prefix[:index]):
                                            prefix_new += char
                                    else:
                                        prefix_new += char

                                if prefix_new:
                                    prefix = '"{} {}"'.format(config.address_tag, prefix_new)
                                else:
                                    prefix = '"{} {}"'.format(config.address_tag, address)

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
        # add subject tag

        header = email.get("Subject").strip()

        if not re.search(r"^{} ".format(re.escape(config.subject_tag)), header):
            header = "{} {}".format(config.subject_tag, header)

            del email["Subject"]
            email["Subject"] = header

            email_modified = True

    if config.text_tag:
        # add text body tag

        try:
            part = extract_part(email, "text/plain")
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.INVALID_ENCODING

        if part is not None:
            (part, charset, content) = part

            if config.text_top:
                content = config.text_tag + content
            else:
                content += config.text_tag

            if charset != CHARSET_UTF8 and not string_ascii(config.text_tag):
                charset = CHARSET_UTF8

            if HEADER_CTE in part:
                del part[HEADER_CTE]

            part.set_payload(content, charset=charset)

            email_modified = True

    if config.html_tag:
        # add html body tag

        try:
            part = extract_part(email, "text/html")
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.INVALID_ENCODING

        if part is not None:
            (part, charset, content) = part

            if config.html_top:
                match = re.search(r"<body[^>]*>", content)

                if match is not None:
                    index = match.end()
                else:
                    match = re.search(r"<html[^>]*>", content)

                    if match is not None:
                        index = match.end()
                    else:
                        index = 0
            else:
                index = content.find("</body>")

                if index < 0:
                    index = content.find("</html>")

                    if index < 0:
                        index = len(content) - 1

            if HEADER_CTE in part:
                del part[HEADER_CTE]

            if charset != CHARSET_UTF8 and not string_ascii(config.html_tag):
                charset = CHARSET_UTF8

            part.set_payload(content[:index] + '<div id="{}">{}</div>'.format(config.html_tag_id, config.html_tag) + content[index:], charset=charset)

            email_modified = True

    if config.calendar_tag:
        # add calendar tag

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
                    else:
                        name = re.search(r"[^:;]*", organizer[name_start:]).group(0)

                    if not re.search(r"^{} ".format(re.escape(config.calendar_tag)), name):
                        if HEADER_CTE in part:
                            del part[HEADER_CTE]

                        if charset != CHARSET_UTF8 and not string_ascii(config.calendar_tag):
                            charset = CHARSET_UTF8

                        part.set_payload(content[:organizer_start + name_start] + config.calendar_tag + " " + content[organizer_start + name_start:], charset=charset)

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
