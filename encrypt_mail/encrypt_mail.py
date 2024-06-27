# encrypt_mail.py V6.2.0
#
# Copyright (c) 2020-2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from re import search, escape, sub, IGNORECASE
from random import choice
from string import ascii_letters, digits, punctuation
from email import message, policy
from email.utils import parseaddr, getaddresses
from smtplib import SMTP

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "keyword_encryption", "password_length", "password_punctuation" )

TEMPLATE_RECIPIENT = "You have received an encrypted email from {} attached to this email.\n\nThe password will be provided to you by the sender shortly.\n\nHave a nice day."
TEMPLATE_SENDER = "The email has been encrypted with the password {} and sent.\n\nPlease provide the recipients with the password.\n\nHave a nice day."

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

    keyword_escaped = escape(config.keyword_encryption)

    if not search(fr"^{keyword_escaped}", header_subject, IGNORECASE):
        return ReturnCode.NONE

    if "From" not in email:
        write_log(log, "From header does not exist")

        return ReturnCode.ERROR

    header_from = str(email["From"])

    if not header_from:
        write_log(log, "From header is empty")

        return ReturnCode.ERROR

    try:
        address_sender = parseaddr(header_from)[1]
    except Exception:
        write_log(log, "Cannot parse From header")

        return ReturnCode.ERROR

    if not address_sender:
        write_log(log, "Cannot find sender address")

        return ReturnCode.ERROR

    address_recipient = dict()

    # collect email addresses in To and Cc headers
    for header_keyword in [ "To", "Cc" ]:
        if header_keyword in email:
            try:
                list_address = getaddresses(email.get_all(header_keyword))
            except Exception:
                write_log(log, f"Cannot parse '{header_keyword}' header")

                return ReturnCode.ERROR

            address_recipient[header_keyword] = { address for (_, address) in list_address }

    if "To" not in address_recipient:
        write_log(log, "Cannot find recipient address")

        return ReturnCode.ERROR

    # remove encryption keyword from subject header
    email = sub(fr"(\n|^)Subject: *{keyword_escaped} *", r"\1Subject: ", email.as_string(), count=1, flags=IGNORECASE)
    header_subject = sub(fr"^{keyword_escaped} *", "", header_subject, flags=IGNORECASE)

    password_characters = ascii_letters + digits

    if config.password_punctuation:
        password_characters += punctuation

    password = "".join(choice(password_characters) for _ in range(config.password_length))

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

    email_message.set_content(TEMPLATE_RECIPIENT.format(address_sender))
    email_message.add_attachment(zip_archive, maintype="application", subtype="zip", filename="email.zip")

    try:
        with SMTP("localhost", port=PORT_SMTP) as s:
            s.send_message(email_message)
    except Exception:
        write_log(log, "Cannot send recipient email")

        return ReturnCode.ERROR

    # send email with password to sender
    email_message = message.EmailMessage(policy=policy.SMTP)

    email_message["Subject"] = f"Re: {header_subject}"
    email_message["From"] = address_sender
    email_message["To"] = address_sender

    email_message.set_content(TEMPLATE_SENDER.format(password))

    try:
        with SMTP("localhost", port=PORT_SMTP) as s:
            s.send_message(email_message)
    except Exception:
        write_log(log, "Cannot send sender email")

    return ReturnCode.DETECTED
