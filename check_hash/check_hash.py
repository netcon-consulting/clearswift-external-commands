# check_hash.py V1.0.0
#
# Copyright (c) 2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from hashlib import md5, sha256

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "md5_hashes", "sha256_hashes" )

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Check MD5 and SHA-256 hashes of attachments against list of known malicious hashes.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    :type disable_splitting: bool
    :type reformat_header: bool
    """
    if not (config.md5_hashes or config.sha256_hashes):
        return ReturnCode.NONE

    try:
        email = read_email(input, disable_splitting)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    if config.md5_hashes:
        try:
            set_md5 = { hash.lower() for hash in set(lexical_list(config.md5_hashes)) }
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.ERROR
    else:
        set_md5 = set()

    if config.sha256_hashes:
        try:
            set_sha256 = { hash.lower() for hash in set(lexical_list(config.sha256_hashes)) }
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.ERROR
    else:
        set_sha256 = set()

    for part in email.walk():
        if part.is_attachment():
            data = part.get_payload(decode=True)

            if set_md5 and md5(data).hexdigest() in set_md5:
                found = "MD5"
            elif set_sha256 and sha256(data).hexdigest() in set_sha256:
                found = "SHA-256"
            else:
                found = None

            if found is not None:
                write_log(log, f"{found} {part.get_filename()}")

                return ReturnCode.DETECTED

    return ReturnCode.NONE
