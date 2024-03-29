# encrypt_mail.py V6.1.1
#
# Copyright (c) 2020-2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
import random
import string
from email import message, policy
from email.utils import parseaddr, getaddresses
import smtplib

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "keyword_encryption", "password_length", "password_punctuation" )

MESSAGE_RECIPIENT="You have received an encrypted email from {} attached to this email.\n\nThe password will be provided to you by the sender shortly.\n\nHave a nice day."
MESSAGE_SENDER="The email has been encrypted with the password {} and sent.\n\nPlease provide the recipients with the password.\n\nHave a nice day."

PORT_SMTP=10026

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Zip-encrypt email if trigger keyword present in subject header and send it to recipients and generated password to sender.

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

        return ReturnCode.ERROR

    if "Subject" not in email:
        return ReturnCode.NONE

    header_subject = str(email["Subject"])

    keyword_escaped = re.escape(config.keyword_encryption)

    if not re.match(r"^{}".format(keyword_escaped), header_subject, re.IGNORECASE):
        return ReturnCode.NONE

    if "From" not in email:
        write_log(log, "Header from does not exist")

        return ReturnCode.ERROR

    header_from = str(email["From"])

    if not header_from:
        write_log(log, "Header from is empty")

        return ReturnCode.ERROR

    address_sender = parseaddr(header_from)[1]

    if not address_sender:
        write_log(log, "Cannot find sender address")

        return ReturnCode.ERROR

    address_recipient = dict()

    # collect email addresses in To and Cc headers
    for header_keyword in [ "To", "Cc" ]:
        if header_keyword in email:
            address_recipient[header_keyword] = { address for (_, address) in getaddresses(email.get_all(header_keyword)) }

    if "To" not in address_recipient:
        write_log(log, "Cannot find recipient address")

        return ReturnCode.ERROR

    # remove encryption keyword from subject header
    email = re.sub(r"(\n|^)Subject: *{} *".format(keyword_escaped), r"\1Subject: ", email.as_string(), count=1, flags=re.IGNORECASE)
    header_subject = re.sub(r"^{} *".format(keyword_escaped), "", header_subject, flags=re.IGNORECASE)

    password_characters = string.ascii_letters + string.digits
    if config.password_punctuation:
        password_characters += string.punctuation
    password = "".join(random.choice(password_characters) for i in range(config.password_length))

    try:
        zip_archive = zip_encrypt({ ("email.eml", email) }, password)
    except Exception:
        write_log(log, "Error zip-encrypting email")

        return ReturnCode.ERROR

    # send email with encrypted original mail attached to recipients
    email_message = message.EmailMessage(policy=policy.SMTP)
    email_message["Subject"] = header_subject
    email_message["From"] = address_sender
    email_message["To"] = ", ".join(address_recipient["To"])
    if "Cc" in address_recipient:
        email_message["Cc"] = ", ".join(address_recipient["Cc"])
    email_message.set_content(MESSAGE_RECIPIENT.format(address_sender))
    email_message.add_attachment(zip_archive, maintype="application", subtype="zip", filename="email.zip")

    try:
        with smtplib.SMTP("localhost", port=PORT_SMTP) as s:
            s.send_message(email_message)
    except Exception:
        write_log(log, "Cannot send recipient email")

        return ReturnCode.ERROR

    # send email with password to sender
    email_message = message.EmailMessage(policy=policy.SMTP)
    email_message["Subject"] = "Re: {}".format(header_subject)
    email_message["From"] = address_sender
    email_message["To"] = address_sender
    email_message.set_content(MESSAGE_SENDER.format(password))

    try:
        with smtplib.SMTP("localhost", port=PORT_SMTP) as s:
            s.send_message(email_message)
    except Exception:
        write_log(log, "Cannot send sender email")

    return ReturnCode.DETECTED
