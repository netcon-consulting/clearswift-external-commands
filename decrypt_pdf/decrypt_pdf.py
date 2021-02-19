#!/usr/bin/env python3

# decrypt_pdf_file.py V1.0.0
#
# Copyright (c) 2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

from tempfile import NamedTemporaryFile
from shutil import copyfile
import fitz
from netcon import ParserArgs, get_config, write_log, get_expression_list, scan_sophos, scan_kaspersky, scan_avira

DESCRIPTION = "attempts to decrypt PDF using a provided list of passwords and optionally scans contents with AV and removes encryption"

@enum.unique
class ReturnCode(enum.IntEnum):
    """
    Return code.

    0   - decryption successful
    1   - decryption failed or virus found
    2   - encryption successfully removed
    99  - error
    255 - unhandled exception
    """
    SUCCESS = 0
    PROBLEM = 1
    DECRYPTED = 2
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "name_expression_list", "scan_sophos", "scan_kaspersky", "scan_avira", "remove_encryption" )

def main(args):
    try:
        config = get_config(args.config, CONFIG_PARAMETERS)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    try:
        set_password = get_expression_list(config.name_expression_list)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    if not set_password:
        write_log(args.log, "Password list is empty")

        return ReturnCode.ERROR

    try:
        pdf_file = fitz.open(args.input)
    except:
        write_log(args.log, "Cannot open PDF file '{}'".format(args.input))

        return ReturnCode.ERROR

    for password in set_password:
        if pdf_file.authenticate(password) != 0:
            break
    else:
        write_log(args.log, "Decryption failed")

        return ReturnCode.PROBLEM

    list_scan = list()

    if config.scan_sophos:
        list_scan.append(scan_sophos)

    if config.scan_kaspersky:
        list_scan.append(scan_kaspersky)

    if config.scan_avira:
        list_scan.append(scan_avira)

    if list_scan or config.remove_encryption:
        virus_found = None

        with NamedTemporaryFile(dir="/tmp") as path_tmpfile:
            path_file = path_tmpfile.name

            pdf_file.save(path_file)

            pdf_file.close()

            for scan in list_scan:
                try:
                    virus_found = scan(path_file)
                except Exception as ex:
                    write_log(args.log, ex)

                    return ReturnCode.ERROR

                if virus_found is not None:
                    break

            if virus_found is not None:
                write_log(args.log, "Virus '{}'".format(virus_found))

                return ReturnCode.PROBLEM

            if config.remove_encryption:
                copyfile(path_file, args.input)

                return ReturnCode.DECRYPTED

    return ReturnCode.SUCCESS

#########################################################################################

if __name__ == "__main__":
    parser = ParserArgs(DESCRIPTION, config=bool(CONFIG_PARAMETERS))

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
