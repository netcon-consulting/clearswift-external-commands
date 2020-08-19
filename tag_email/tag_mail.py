#!/usr/bin/env python3

# tag_mail.py V1.0.0
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import argparse
import re
from netcon import read_config, read_email, write_log, extract_addresses

DESCRIPTION = "adds tags to from- and subject-header and removes tags from to/cc- and subject-header"

class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0  - email not email_modified
    1  - tag added
    99 - error
    255 - unhandled exception
    """
    NOT_MODIFIED = 0
    TAG_ADDED = 1
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "tag_address", "tag_subject" )

def add_tag_address(tag, header):
    """
    Add tag to from header.

    :type tag: str
    :type header: str
    :rtype: str
    """
    PATTERN_TAG = re.compile(r'^"{} '.format(re.escape(tag)))

    list_address = extract_addresses(header)

    if not list_address:
        raise Exception("Cannot find email address in header")

    (prefix, email, suffix) = list_address[0]

    if prefix.endswith("<") and suffix.startswith(">"):
        prefix = prefix[:-1]
        suffix = suffix[1:]

    prefix = prefix.strip()
    suffix = suffix.strip()

    if re.search(PATTERN_TAG, prefix):
        return header
    else:
        prefix_new = ""

        for (index, char) in enumerate(prefix):
            if char == '"':
                if end_escape(prefix[:index]):
                    prefix_new += char
            else:
                prefix_new += char

        return '"{} {}"'.format(tag, prefix_new) + " <" + email + "> " + suffix

def remove_tag_address(tag, header):
    """
    Remove tag from to/cc header.

    :type tag: str
    :type header: str
    :rtype: str
    """
    PATTERN_TAG = re.compile(r'^"{} '.format(re.escape(tag)))

    list_address = extract_addresses(header)

    if not list_address:
        raise Exception("Cannot find email address in header")

    header = ""

    for (prefix, email, suffix) in list_address:
        if prefix.startswith(";") or prefix.startswith(","):
            prefix = prefix[1:]

        if prefix.endswith("<") and suffix.startswith(">"):
            prefix = prefix[:-1]
            suffix = suffix[1:]

        prefix = prefix.strip()
        suffix = suffix.strip()

        prefix = re.sub(PATTERN_TAG, '"', prefix)

        if prefix:
            header += prefix + " "

        header += "<" + email + ">"

        if suffix:
            header += " " + suffix

        header += "; "

    return header[:-2]

def add_tag_subject(tag, header):
    """
    Add tag to subject header.

    :type tag: str
    :type header: str
    :rtype: str
    """
    PATTERN_TAG = re.compile(r'^{} '.format(re.escape(tag)))

    header_strip = header.strip()

    if re.search(PATTERN_TAG, header_strip):
        return header
    else:
        return "{} {}".format(tag, header_strip)

def remove_tag_subject(tag, header):
    """
    Remove tag from subject header.

    :type tag: str
    :type header: str
    :rtype: str
    """
    PATTERN_TAG = re.compile(r'^{} '.format(re.escape(tag)))

    return re.sub(PATTERN_TAG, "", header)

def main(args):
    try:
        config = read_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    email_modified = False

    if args.remove:
        if config.tag_address:
            for header_keyword in [ "To", "Cc" ]:
                list_header = email.get_all(header_keyword)

                if list_header:
                    header_joined = ""
                    header_changed = False

                    for header_org in list_header:
                        header_new = remove_tag_address(config.tag_address, header_org)

                        if header_new != header_org:
                            header_changed = True

                        header_joined += header_new + "; "

                    if header_changed:
                        email_modified = True
                        email.__delitem__(header_keyword)
                        email[header_keyword] = header_joined[:-2]

        if config.tag_subject and "Subject" in email:
            header_org = email["Subject"]

            header_new = remove_tag_subject(config.tag_subject, header_org)

            if header_new != header_org:
                email_modified = True
                email.__delitem__("Subject")
                email["Subject"] = header_new
    else:
        if config.tag_address and "From" in email:
            header_org = email["From"]

            header_new = add_tag_address(config.tag_address, header_org)

            if header_new != header_org:
                email_modified = True
                email.__delitem__("From")
                email["From"] = header_new

        if config.tag_subject and "Subject" in email:
            header_org = email["Subject"]

            header_new = add_tag_subject(config.tag_subject, header_org)

            if header_new != header_org:
                email_modified = True
                email.__delitem__("Subject")
                email["Subject"] = header_new

    if email_modified:
        try:
            with open(args.input, "w") as f:
                f.write(email.as_string())
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
