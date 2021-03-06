#!/usr/bin/env python3

# tag_mail.py V6.1.1
#
# Copyright (c) 2020-2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import re
from email.header import decode_header, make_header
import bs4
from netcon import ParserArgs, get_config, read_email, write_log, end_escape, extract_addresses, get_address_list, string_ascii, python_charset, CHARSET_UTF8

DESCRIPTION = "add and remove tags in address and subject headers, text and html bodies and calendar objects"

RECURSION_LIMIT = 5000

@enum.unique
class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0   - email not modified
    1   - invalid character encoding
    2   - tag(s) added/removed
    99  - error
    255 - unhandled exception
    """
    NOT_MODIFIED = 0
    INVALID_ENCODING = 1
    TAG_ADDED = 2
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "address_tag", "name_domain_list", "clean_text", "clean_html", "subject_tag", "text_tag", "text_top", "html_tag", "html_top", "html_tag_id", "calendar_tag" )

CODE_SKIPPED = ReturnCode.NOT_MODIFIED

def main(args):
    HEADER_CTE = "Content-Transfer-Encoding"

    try:
        config = get_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    sys.setrecursionlimit(RECURSION_LIMIT)

    if config.text_tag or (args.remove and config.address_tag and config.clean_text):
        text_part = None

        for part in email.walk():
            if part.get_content_type() == "text/plain" and not part.is_attachment():
                text_part = part
                text_charset = python_charset(text_part.get_content_charset())

                if text_charset is None:
                    text_charset = CHARSET_UTF8

                try:
                    text_content = text_part.get_payload(decode=True).decode(text_charset, errors="ignore").replace("\r", "")
                except Exception:
                    write_log(args.log, "Cannot decode text part with charset '{}'".format(text_charset))

                    return ReturnCode.INVALID_ENCODING

                break

    if config.html_tag or (args.remove and config.address_tag and config.clean_html):
        html_part = None

        for part in email.walk():
            if part.get_content_type() == "text/html" and not part.is_attachment():
                html_part = part
                html_charset = python_charset(html_part.get_content_charset())

                if html_charset is None:
                    html_charset = CHARSET_UTF8

                try:
                    html_content = html_part.get_payload(decode=True).decode(html_charset, errors="ignore")
                except Exception:
                    write_log(args.log, "Cannot decode html part with charset '{}'".format(html_charset))

                    return ReturnCode.INVALID_ENCODING

                break

    if config.calendar_tag:
        calendar_part = None

        for part in email.walk():
            if part.get_content_type() == "text/calendar" and not part.is_attachment():
                calendar_part = part
                calendar_charset = python_charset(calendar_part.get_content_charset())

                if calendar_charset is None:
                    calendar_charset = CHARSET_UTF8

                try:
                    calendar_content = calendar_part.get_payload(decode=True).decode(calendar_charset, errors="ignore")
                except Exception:
                    write_log(args.log, "Cannot decode calendar part with charset '{}'".format(calendar_charset))

                    return ReturnCode.INVALID_ENCODING

                break

    email_modified = False

    if args.remove:
        if config.address_tag:
            # remove address tag

            string_tag = "{} ".format(config.address_tag)

            pattern_tag = re.compile(r'^"?{} '.format(re.escape(config.address_tag)))

            pattern_quote = re.compile(r'^".*"$')

            for header_keyword in [ "To", "Cc" ]:
                if header_keyword in email:
                    header = "".join([ part if isinstance(part, str) else part.decode(python_charset(encoding), errors="ignore") if encoding else part.decode(CHARSET_UTF8, errors="ignore") for (part, encoding) in decode_header(", ".join([ str(header) for header in email.get_all(header_keyword) ]).replace("\n", "")) ])

                    list_address = extract_addresses(header)

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

                            if not string_ascii(prefix):
                                if re.search(pattern_quote, prefix):
                                    prefix = prefix[1:-1]

                                prefix = make_header([ ( prefix.encode(CHARSET_UTF8), CHARSET_UTF8 ) ]).encode()

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

            header = "".join([ part if isinstance(part, str) else part.decode(python_charset(encoding), errors="ignore") if encoding else part.decode(CHARSET_UTF8, errors="ignore") for (part, encoding) in decode_header(str(email.get("Subject")).strip().replace("\n", "")) ])

            match = re.search(r"{} ".format(re.escape(config.subject_tag)), header)

            if match is not None:
                del email["Subject"]
                email["Subject"] = header[:match.start()] + header[match.end():]

                email_modified = True

        if (config.text_tag or (config.address_tag and config.clean_text)) and text_part is not None:
            # remove text body tag

            body_modified = False

            if config.text_tag:
                split_tag = config.text_tag.split("\n")

                while not split_tag[-1]:
                    del split_tag[-1]

                pattern_tag = re.compile("\\n".join([ r"(>+ )*" + re.escape(item) for item in split_tag ]) + r"\n")

                match = re.search(pattern_tag, text_content)

                if match is not None:
                    text_content = re.sub(pattern_tag, "", text_content)

                    body_modified = True

            if config.address_tag and config.clean_text and string_tag in text_content:
                text_content = text_content.replace(string_tag, "")

                body_modified = True

            if body_modified:
                if HEADER_CTE in text_part:
                    del text_part[HEADER_CTE]

                text_part.set_payload(text_content, charset=text_charset)

                email_modified = True

        if (config.html_tag or (config.address_tag and config.clean_html)) and html_part is not None:
            # remove html body tag

            body_modified = False

            soup = bs4.BeautifulSoup(html_content, features="html5lib")

            list_tag = soup.find_all("div", id=re.compile(r".*{}.*".format(re.escape(config.html_tag_id))))

            if list_tag:
                for tag in list_tag:
                    tag.decompose()

                try:
                    html_content = soup.encode(html_charset).decode(html_charset)
                except Exception:
                    write_log(args.log, "Error converting soup to string")

                    return ReturnCode.ERROR

                body_modified = True

            if config.address_tag and config.clean_html and string_tag in html_content:
                html_content = html_content.replace(string_tag, "")

                body_modified = True

            if body_modified:
                if HEADER_CTE in html_part:
                    del html_part[HEADER_CTE]

                html_part.set_payload(html_content, charset=html_charset)

                email_modified = True

        if config.calendar_tag and calendar_part is not None:
            # remove calendar tag

            match = re.search(r"\nORGANIZER;.*CN=([^:;\r\n]+)", calendar_content)

            if match is not None:
                organizer = match.group(1)
                organizer_start = match.start(1)
                organizer_end = match.end(1)

                match = re.search(r"^{} ".format(re.escape(config.calendar_tag)), organizer)

                if match is not None:
                    if HEADER_CTE in calendar_part:
                        del calendar_part[HEADER_CTE]

                    if calendar_charset != CHARSET_UTF8 and not string_ascii(config.calendar_tag):
                        calendar_charset = CHARSET_UTF8

                    calendar_part.set_payload(calendar_content[:organizer_start] + organizer[match.end():] + calendar_content[organizer_end:], charset=calendar_charset)

                    email_modified = True
    else:
        if config.address_tag and "From" in email:
            # add address tag

            pattern_tag = re.compile(r'^"?{} '.format(re.escape(config.address_tag)))

            pattern_quote = re.compile(r'^".*"$')

            list_address = extract_addresses("".join([ part if isinstance(part, str) else part.decode(python_charset(encoding), errors="ignore") if encoding else part.decode(CHARSET_UTF8, errors="ignore") for (part, encoding) in decode_header(str(email.get("From")).replace("\n", "")) ]))

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

                    if not string_ascii(prefix):
                        if re.search(pattern_quote, prefix):
                            prefix = prefix[1:-1]

                        prefix = make_header([ ( prefix.encode(CHARSET_UTF8), CHARSET_UTF8 ) ]).encode()

                    del email["From"]
                    email["From"] = prefix + " <" + address + "> " + suffix

                    email_modified = True

            if config.name_domain_list:
                # add address tag to external addresses in To/Cc header

                try:
                    set_address = get_address_list(config.name_domain_list)
                except Exception as ex:
                    write_log(args.log, ex)

                    return ReturnCode.ERROR

                pattern_domain = re.compile(r"^\S+@(\S+)")

                set_domain = { match.group(1).lower() for match in [ re.search(pattern_domain, address) for address in set_address ] if match is not None }

                for header_keyword in [ "To", "Cc" ]:
                    if header_keyword in email:
                        header = "".join([ part if isinstance(part, str) else part.decode(python_charset(encoding), errors="ignore") if encoding else part.decode(CHARSET_UTF8, errors="ignore") for (part, encoding) in decode_header(", ".join([ str(header) for header in email.get_all(header_keyword) ]).replace("\n", "")) ])

                        list_address = extract_addresses(header)

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

                                if not string_ascii(prefix):
                                    if re.search(pattern_quote, prefix):
                                        prefix = prefix[1:-1]

                                    prefix = make_header([ ( prefix.encode(CHARSET_UTF8), CHARSET_UTF8 ) ]).encode()

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

            header = "".join([ part if isinstance(part, str) else part.decode(python_charset(encoding), errors="ignore") if encoding else part.decode(CHARSET_UTF8, errors="ignore") for (part, encoding) in decode_header(str(email.get("Subject")).strip().replace("\n", "")) ])

            if not re.search(r"^{} ".format(re.escape(config.subject_tag)), header):
                header = "{} {}".format(config.subject_tag, header)

                del email["Subject"]
                email["Subject"] = header

                email_modified = True

        if config.text_tag and text_part is not None:
            # add text body tag

            if config.text_top:
                text_content = config.text_tag + text_content
            else:
                text_content += config.text_tag

            if text_charset != CHARSET_UTF8 and not string_ascii(config.text_tag):
                text_charset = CHARSET_UTF8

            if HEADER_CTE in text_part:
                del text_part[HEADER_CTE]

            text_part.set_payload(text_content, charset=text_charset)

            email_modified = True

        if config.html_tag and html_part is not None:
            # add html body tag

            if config.html_top:
                match = re.search(r"<body[^>]*>", html_content)

                if match is not None:
                    index = match.end()
                else:
                    match = re.search(r"<html[^>]*>", html_content)

                    if match is not None:
                        index = match.end()
                    else:
                        index = 0
            else:
                index = html_content.find("</body>")

                if index < 0:
                    index = html_content.find("</html>")

                    if index < 0:
                        index = len(html_content) - 1

            if HEADER_CTE in html_part:
                del html_part[HEADER_CTE]

            if html_charset != CHARSET_UTF8 and not string_ascii(config.html_tag):
                html_charset = CHARSET_UTF8

            html_part.set_payload(html_content[:index] + '<div id="{}">{}</div>'.format(config.html_tag_id, config.html_tag) + html_content[index:], charset=html_charset)

            email_modified = True

        if config.calendar_tag and calendar_part is not None:
            # add calendar tag

            match = re.search(r"\nORGANIZER;.*CN=([^:;\r\n]+)", calendar_content)

            if match is not None:
                organizer = match.group(1)

                if not re.search(r"^{} ".format(re.escape(config.calendar_tag)), organizer):
                    if HEADER_CTE in calendar_part:
                        del calendar_part[HEADER_CTE]

                    if calendar_charset != CHARSET_UTF8 and not string_ascii(config.calendar_tag):
                        calendar_charset = CHARSET_UTF8

                    calendar_part.set_payload(calendar_content[:match.start(1)] + config.calendar_tag + " " + organizer + calendar_content[match.end(1):], charset=calendar_charset)

                    email_modified = True

    if email_modified:
        try:
            with open(args.input, "wb") as f:
                f.write(email.as_bytes())
        except Exception:
            write_log(args.log, "Error writing '{}'".format(args.input))

            return ReturnCode.ERROR

        return ReturnCode.TAG_ADDED

    return ReturnCode.NOT_MODIFIED

#########################################################################################

if __name__ == "__main__":
    parser = ParserArgs(DESCRIPTION, bool(CONFIG_PARAMETERS), CODE_SKIPPED is not None)
    parser.add_argument("-r", "--remove", action="store_true", help="remove tags")

    args = parser.parse_args()

    if CODE_SKIPPED is not None and args.type != "Message":
        # skip embedded/attached SMTP messages
        sys.exit(CODE_SKIPPED)

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
