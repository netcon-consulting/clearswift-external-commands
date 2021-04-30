#!/usr/bin/env python3

# decrypt_zip.py V2.0.2
#
# Copyright (c) 2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

from pathlib import Path
from io import BytesIO
from tempfile import TemporaryDirectory
import pyzipper
from netcon import ParserArgs, get_config, write_log, get_expression_list, scan_sophos, scan_kaspersky, scan_avira, CHARSET_UTF8

DESCRIPTION = "attempt to decrypt ZIP container using a provided list of passwords and optionally scan contents with AV and removes encryption"

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

    list_scan = list()

    if config.scan_sophos:
        list_scan.append(scan_sophos)

    if config.scan_kaspersky:
        list_scan.append(scan_kaspersky)

    if config.scan_avira:
        list_scan.append(scan_avira)

    virus_found = None

    if config.remove_encryption:
        buffer = BytesIO()

        zf_decrypted = pyzipper.AESZipFile(buffer, "w", compression=pyzipper.ZIP_LZMA)

    with TemporaryDirectory(dir="/tmp") as path_tmpdir:
        path_tmpdir = Path(path_tmpdir)

        if config.scan_avira:
            path_tmpdir.chmod(0o755)

        with pyzipper.AESZipFile(args.input, "r", compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
            for password in set_password:
                try:
                    zf.pwd = password.encode(CHARSET_UTF8)

                    for file_name in zf.namelist():
                        path_file = path_tmpdir.joinpath(file_name)

                        data = zf.read(file_name)

                        try:
                            with open(path_file, "wb") as f:
                                f.write(data)
                        except Exception:
                            write_log(args.log, "Cannot extract file '{}'".format(file_name))

                            return ReturnCode.ERROR

                        path_file = str(path_file)

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
                            zf_decrypted.writestr(file_name, data)

                    break
                except RuntimeError:
                    pass
            else:
                write_log(args.log, "Decryption failed")

                return ReturnCode.PROBLEM

    if config.remove_encryption:
        zf_decrypted.close()

        with open(args.input, "wb") as f:
            f.write(buffer.getvalue())

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
