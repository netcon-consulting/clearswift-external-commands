# decrypt_pdf.py V2.0.0
#
# Copyright (c) 2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from tempfile import NamedTemporaryFile
from shutil import copyfile
import fitz

ADDITIONAL_ARGUMENTS = ( )
CONFIG_PARAMETERS = ( "name_expression_list", "scan_sophos", "scan_kaspersky", "scan_avira", "remove_encryption" )

def run_command(input, log, config, additional):
    """
    Attempt to decrypt PDF using a provided list of passwords and optionally scan contents with AV and removes encryption.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    """
    try:
        set_password = get_expression_list(config.name_expression_list)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    if not set_password:
        write_log(log, "Password list is empty")

        return ReturnCode.ERROR

    try:
        pdf_file = fitz.open(input)
    except Exception:
        write_log(log, "Cannot open PDF file '{}'".format(input))

        return ReturnCode.ERROR

    for password in set_password:
        if pdf_file.authenticate(password) != 0:
            break
    else:
        write_log(log, "Decryption failed")

        return ReturnCode.DETECTED

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
                    write_log(log, ex)

                    return ReturnCode.ERROR

                if virus_found is not None:
                    break

            if virus_found is not None:
                write_log(log, "Virus '{}'".format(virus_found))

                return ReturnCode.DETECTED

            if config.remove_encryption:
                copyfile(path_file, input)

                return ReturnCode.MODIFIED

    return ReturnCode.NONE
