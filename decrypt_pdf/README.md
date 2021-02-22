decrypt_pdf.py V1.0.0
=====================

Attempts to decrypt PDF using a provided list of passwords and optionally scans contents with AV and removes encryption.

## Parameters
* name_expression_list (string): name of lexical expression list with passwords
* scan_sophos (boolean): scan contents with Sophos AV
* scan_kaspersky (boolean): scan contents with Kaspersky AV
* scan_avira (boolean): scan contents with Avira AV
* remove_encryption (boolean): remove encryption from PDF

## Lexical expression lists
* Decrypt PDF passwords: list of passwords

## Hold Areas
* Decrypt PDF: mails with PDFs that cannot be decrypted with any of the provided passwords or contain a virus