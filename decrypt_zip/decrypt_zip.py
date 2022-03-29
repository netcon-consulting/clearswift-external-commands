# decrypt_zip.py V5.0.0
#
# Copyright (c) 2021-2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from pathlib import Path
from io import BytesIO
from tempfile import TemporaryDirectory
import pyzipper

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "password_list", "scan_sophos", "scan_kaspersky", "scan_avira", "remove_encryption" )

def run_command(input, log, config, additional, optional):
    """
    Attempt to decrypt ZIP container using a provided list of passwords and optionally scan contents with AV and removes encryption.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    """
    try:
        set_password = set(lexical_list(config.password_list))
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    if not set_password:
        write_log(log, "Password list is empty")

        return ReturnCode.DETECTED

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

        with pyzipper.AESZipFile(input, "r", compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
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
                            write_log(log, "Cannot extract file '{}'".format(file_name))

                            return ReturnCode.DETECTED

                        path_file = str(path_file)

                        for scan in list_scan:
                            try:
                                virus_found = scan(path_file)
                            except Exception as ex:
                                write_log(log, ex)

                                return ReturnCode.DETECTED

                            if virus_found is not None:
                                break

                        if virus_found is not None:
                            write_log(log, "Virus '{}'".format(virus_found))

                            return ReturnCode.DETECTED

                        if config.remove_encryption:
                            zf_decrypted.writestr(file_name, data)

                    break
                except RuntimeError:
                    pass
            else:
                write_log(log, "Decryption failed")

                return ReturnCode.DETECTED

    if config.remove_encryption:
        zf_decrypted.close()

        with open(input, "wb") as f:
            f.write(buffer.getvalue())

        return ReturnCode.MODIFIED

    return ReturnCode.NONE
