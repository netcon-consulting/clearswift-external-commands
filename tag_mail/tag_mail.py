#!/usr/bin/env python3

# tag_mail.py V2.1.6
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import argparse
import re
import bs4
from email.header import decode_header, make_header
from netcon import read_config, read_email, write_log, end_escape, extract_addresses, get_address_list, string_ascii

DESCRIPTION = "adds/removes tags to/from address and subject headers and text and html bodies"

class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0   - email not modified
    1   - tag(s) added
    99  - error
    255 - unhandled exception
    """
    NOT_MODIFIED = 0
    TAG_ADDED = 1
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "address_tag", "name_domain_list", "subject_tag", "text_tag", "text_position", "html_tag", "html_position", "html_tag_id" )

def main(args):
    try:
        config = read_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    if config.text_tag:
        part_text = None

        for part in email.walk():
            if part.get_content_type() == "text/plain":
                part_text = part
                content_text = part_text.get_payload(decode=True).decode("utf-8", errors="ignore")

                break

    if config.html_tag:
        part_html = None

        for part in email.walk():
            if part.get_content_type() == "text/html":
                part_html = part
                content_html = part_html.get_payload(decode=True).decode("utf-8", errors="ignore")
                soup = bs4.BeautifulSoup(content_html, features="html5lib")

                break

    email_modified = False

    if args.remove:
        if config.address_tag:
            # remove address tag

            pattern = re.compile(r'^"{} '.format(re.escape(config.address_tag)))

            for header_keyword in [ "To", "Cc" ]:
                if header_keyword in email:
                    header = "".join([ part if isinstance(part, str) else part.decode(encoding, errors="ignore") if encoding else part.decode("utf-8", errors="ignore") for (part, encoding) in decode_header("; ".join([ str(header) for header in email.get_all(header_keyword) ]).replace("\n", "")) ])

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

                            match = re.search(pattern, prefix)

                            if match:
                                prefix = '"' + prefix[len(config.address_tag) + 2:]

                                header_modified = True

                            if not string_ascii(prefix):
                                prefix = make_header([ ( prefix.encode("utf-8"), "utf-8" ) ]).encode()

                            if prefix:
                                header += prefix + " "

                            header += "<" + address + ">"

                            if suffix:
                                header += " " + suffix

                            header += "; "

                        if header_modified:
                            del email[header_keyword]
                            email[header_keyword] = header[:-2]

                            email_modified = True

        if config.subject_tag and "Subject" in email:
            # remove subject tag

            header = "".join([ part if isinstance(part, str) else part.decode(encoding, errors="ignore") if encoding else part.decode("utf-8", errors="ignore") for (part, encoding) in decode_header(str(email.get("Subject")).strip().replace("\n", "")) ])

            match = re.search(r"{} ".format(re.escape(config.subject_tag)), header)

            if match:
                del email["Subject"]
                email["Subject"] = header[:match.start()] + header[match.end():]

                email_modified = True

        if config.text_tag and part_text is not None and config.text_tag in content_text:
            # remove text body tag

            part_text.set_payload(content_text.replace(config.text_tag, ""))

            email_modified = True

        if config.html_tag and part_html is not None:
            # remove html body tag

            list_tag = soup.find_all("div", id=config.html_tag_id)

            if list_tag:
                for tag in list_tag:
                    tag.decompose()

                part_html.set_payload(str(soup))

                email_modified = True
    else:
        if config.address_tag and "From" in email:
            # add address tag

            list_address = extract_addresses("".join([ part if isinstance(part, str) else part.decode(encoding, errors="ignore") if encoding else part.decode("utf-8", errors="ignore") for (part, encoding) in decode_header(str(email.get("From")).replace("\n", "")) ]))

            if list_address:
                (prefix, address, suffix) = list_address[0]

                if prefix.endswith("<") and suffix.startswith(">"):
                    prefix = prefix[:-1]
                    suffix = suffix[1:]

                prefix = prefix.strip()
                suffix = suffix.strip()

                if not re.search(r'^"{} '.format(re.escape(config.address_tag)), prefix):
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
                        prefix = make_header([ ( prefix.encode("utf-8"), "utf-8" ) ]).encode()

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

                pattern_tag = re.compile(r'^"{} '.format(re.escape(config.address_tag)))

                for header_keyword in [ "To", "Cc" ]:
                    if header_keyword in email:
                        header = "".join([ part if isinstance(part, str) else part.decode(encoding, errors="ignore") if encoding else part.decode("utf-8", errors="ignore") for (part, encoding) in decode_header("; ".join([ str(header) for header in email.get_all(header_keyword) ]).replace("\n", "")) ])

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
                                    prefix = make_header([ ( prefix.encode("utf-8"), "utf-8" ) ]).encode()

                                if prefix:
                                    header += prefix + " "

                                header += "<" + address + ">"

                                if suffix:
                                    header += " " + suffix

                                header += "; "

                            if header_modified:
                                del email[header_keyword]
                                email[header_keyword] = header[:-2]

                                email_modified = True

        if config.subject_tag and "Subject" in email:
            # add subject tag

            header = "".join([ part if isinstance(part, str) else part.decode(encoding, errors="ignore") if encoding else part.decode("utf-8", errors="ignore") for (part, encoding) in decode_header(str(email.get("Subject")).strip().replace("\n", "")) ])

            if not re.search(r"^{} ".format(re.escape(config.subject_tag)), header):
                header = "{} {}".format(config.subject_tag, header)

                del email["Subject"]
                email["Subject"] = header

                email_modified = True

        if config.text_tag and part_text is not None and config.text_tag not in content_text:
            # add text body tag

            position_lower = config.text_position.lower()

            if position_lower == "top":
                content_text = config.text_tag + content_text
            elif position_lower == "bottom":
                content_text += config.text_tag
            else:
                write_log(args.log, "Invalid tag position '{}'".format(config.text_position))

                return ReturnCode.ERROR

            part_text.set_payload(content_text)

            email_modified = True

        if config.html_tag and part_html is not None and soup.find("div", id=config.html_tag_id) is None:
            # add html body tag

            position_lower = config.html_position.lower()

            if position_lower == "top":
                match = re.search(r"<body[^>]*>", content_html)

                if match:
                    index = match.end(0)
                else:
                    index = -1
            elif position_lower == "bottom":
                index = content_html.find("</body>")
            else:
                write_log(args.log, "Invalid tag position '{}'".format(config.html_position))

                return ReturnCode.ERROR

            if index <= 0:
                write_log(args.log, "Cannot find index of tag position")

                return ReturnCode.ERROR

            part_html.set_payload(content_html[:index] + '<div id="{}">{}</div>'.format(config.html_tag_id, config.html_tag) + content_html[index:])

            email_modified = True

    if email_modified:
        try:
            with open(args.input, "wb") as f:
                f.write(email.as_bytes())
        except:
            write_log(args.log, "Error writing '{}'".format(args.input))

            return ReturnCode.ERROR

        return ReturnCode.TAG_ADDED

    return ReturnCode.NOT_MODIFIED

#########################################################################################

if __name__ == "__main__":
    if __file__.endswith(".py"):
        config_default = __file__[:-3] + ".toml"
    else:
        config_default = __file__ + ".toml"

    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        "-c",
        "--config",
        metavar="CONFIG",
        type=str,
        default=config_default,
        help="path to configuration file (default={})".format(config_default))
    parser.add_argument("input", metavar="INPUT", type=str, help="input file")
    parser.add_argument("log", metavar="LOG", type=str, help="log file")
    parser.add_argument("-r", "--remove", action="store_true", help="remove tags")

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
