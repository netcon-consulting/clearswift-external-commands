#!/usr/bin/env python3

# decrypt_zip.py V1.0.0
#
# Copyright (c) 2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import re
from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import run, PIPE, DEVNULL
import pyzipper
from netcon import ParserArgs, get_config, write_log, get_expression_list, CHARSET_UTF8

DESCRIPTION = "attempts to decrypt zip file using a provided list of passwords and if successful scans contents with Sophos AV"

SOPHOS_EXECUTABLE = '/opt/cs-gateway/bin/sophos/savfiletest'

@enum.unique
class ReturnCode(enum.IntEnum):
    """
    Return code.

    0   - decryption successful
    1   - decryption successful but virus found
    2   - decryption failed
    99  - error
    255 - unhandled exception
    """
    SUCCESS = 0
    VIRUS = 1
    FAILED = 2
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "name_expression_list", )

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

    with TemporaryDirectory(dir="/tmp") as path_tmpdir:
        path_tmpdir = Path(path_tmpdir)

        for password in set_password:
            try:
                with pyzipper.AESZipFile(args.input, "r", compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
                    zf.pwd = password.encode(CHARSET_UTF8)

                    for file_name in zf.namelist():
                        path_file = path_tmpdir.joinpath(file_name)

                        data = zf.read(file_name)

                        try:
                            with open(path_file, "wb") as f:
                                f.write(data)
                        except:
                            write_log(args.log, "Cannot extract file '{}'".format(file_name))

                            return ReturnCode.ERROR

                        try:
                            result = run([ SOPHOS_EXECUTABLE, "-v", "-f", path_file ], check=True, stdout=PIPE, stderr=DEVNULL, encoding=CHARSET_UTF8)
                        except:
                            write_log(args.log, "Error calling Sophos AV")

                            return ReturnCode.ERROR

                        match = re.search(r"\n\tSophosConnection::recvLine returning VIRUS (\S+) {}\n".format(path_file), result.stdout)

                        if match:
                            write_log(args.log, match.group(1))

                            return ReturnCode.VIRUS

                    return ReturnCode.SUCCESS
            except RuntimeError:
                pass

    return ReturnCode.FAILED

#########################################################################################

if __name__ == "__main__":
    parser = ParserArgs(DESCRIPTION, config=bool(CONFIG_PARAMETERS))

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
