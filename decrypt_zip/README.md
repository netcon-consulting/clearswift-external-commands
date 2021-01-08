decrypt_zip.py V1.0.0
=====================

Attempts to decrypt zip file using a provided list of passwords and if successful scans contents with Sophos AV.

## Parameters
* name_expression_list (string): name of lexical expression list with passwords

## Lexical expression lists
* Decrypt ZIP passwords: list of passwords

## Hold Areas
* ZIP Virus: mails with zip files containing a virus
* ZIP decryption failed: mails with zip files that cannot be decrypted with any of the provided passwords
