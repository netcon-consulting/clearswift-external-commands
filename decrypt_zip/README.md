decrypt_zip.py V7.1.0
=====================

Attempt to decrypt ZIP container using a provided list of passwords and optionally scan contents with AV and removes encryption.

## Parameters
* password_list (string): name of lexical expression list with passwords
* scan_sophos (boolean): scan contents with Sophos AV
* scan_kaspersky (boolean): scan contents with Kaspersky AV
* scan_avira (boolean): scan contents with Avira AV
* remove_encryption (boolean): remove encryption from ZIP container

## Lexical expression lists
* Decrypt ZIP passwords: list of passwords

## Hold Areas
* Decrypt ZIP: mails with errors
