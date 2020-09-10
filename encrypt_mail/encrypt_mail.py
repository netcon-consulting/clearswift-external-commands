#!/usr/bin/env python3

# encrypt_mail.py V1.4.1
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import re
import random
import string
from email.message import EmailMessage
import smtplib
from netcon import ParserArgs, read_config, read_email, write_log, zip_encrypt, extract_email_addresses, extract_email_address

DESCRIPTION = "if keyword present in subject zip-encrypts email, sends it to recipients and generated password to sender"

class ReturnCode(enum.IntEnum):
    """
    Return code.

    0   - encryption skipped
    1   - mail encrypted
    99  - error
    255 - unhandled exception
    """
    ENCRYPTION_SKIPPED = 0
    MAIL_ENCRYPTED = 1
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "keyword_encryption", "password_length", "password_punctuation" )

MESSAGE_RECIPIENT="You have received an encrypted email from {} attached to this email.\n\nThe password will be provided to you by the sender shortly.\n\nHave a nice day."
MESSAGE_SENDER="The email has been encrypted with the password {} and sent.\n\nPlease provide the recipients with the password.\n\nHave a nice day."

PORT_SMTP=10026

def main(args):
    try:
        config = read_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    header_subject = email.get("Subject")

    keyword_escaped = re.escape(config.keyword_encryption)

    if not header_subject or not re.match(r"^{}".format(keyword_escaped), header_subject, re.I):
        return ReturnCode.ENCRYPTION_SKIPPED

    header_from = email.get("From")

    if not header_from:
        write_log(args.log, "Header from is empty")

        return ReturnCode.ERROR

    address_sender = extract_email_address(header_from)

    if not address_sender:
        write_log(args.log, "Cannot find sender address")

        return ReturnCode.ERROR

    address_recipient = dict()

    # collect email addresses in To and Cc headers
    for header_keyword in [ "To", "Cc" ]:
        address_recipient[header_keyword] = set()

        list_header = email.get_all(header_keyword)

        if list_header:
            for header in list_header:
                email_addresses = extract_email_addresses(header)

                if email_addresses:
                    address_recipient[header_keyword] |= email_addresses

    if not address_recipient["To"]:
        write_log(args.log, "Cannot find recipient address")

        return ReturnCode.ERROR

    # remove encryption keyword from subject header
    email = re.sub(r"(\n|^)Subject: *{} *".format(keyword_escaped), r"\1Subject: ", email.as_string(), count=1, flags=re.I)
    header_subject = re.sub(r"^{} *".format(keyword_escaped), "", header_subject, flags=re.I)

    password_characters = string.ascii_letters + string.digits
    if config.password_punctuation:
        password_characters += string.punctuation
    password = "".join(random.choice(password_characters) for i in range(config.password_length))

    try:
        zip_archive = zip_encrypt({ ("email.eml", email) }, password)
    except:
        write_log(args.log, "Error zip-encrypting email")

        return ReturnCode.ERROR

    # send email with encrypted original mail attached to recipients
    email_message = EmailMessage()
    email_message["Subject"] = header_subject
    email_message["From"] = address_sender
    email_message["To"] = ", ".join(address_recipient["To"])
    if address_recipient["Cc"]:
        email_message["Cc"] = ", ".join(address_recipient["Cc"])
    email_message.set_content(MESSAGE_RECIPIENT.format(address_sender))
    email_message.add_attachment(zip_archive, maintype="application", subtype="zip", filename="email.zip")

    try:
        with smtplib.SMTP("localhost", port=PORT_SMTP) as s:
            s.send_message(email_message)
    except:
        write_log(args.log, "Cannot send recipient email")

        return ReturnCode.ERROR

    # send email with password to sender
    email_message = EmailMessage()
    email_message["Subject"] = "Re: {}".format(header_subject)
    email_message["From"] = address_sender
    email_message["To"] = address_sender
    email_message.set_content(MESSAGE_SENDER.format(password))

    try:
        with smtplib.SMTP("localhost", port=PORT_SMTP) as s:
            s.send_message(email_message)
    except:
        write_log(args.log, "Cannot send sender email")

    return ReturnCode.MAIL_ENCRYPTED

#########################################################################################

if __name__ == "__main__":
    if CONFIG_PARAMETERS:
        if __file__.endswith(".py"):
            config_default = __file__[:-3] + ".toml"
        else:
            config_default = __file__ + ".toml"

        parser = ParserArgs(DESCRIPTION, config_default=config_default)
    else:
        parser = ParserArgs(DESCRIPTION)

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
