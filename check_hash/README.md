check_hash.py V1.0.0
====================

Check MD5 and SHA-256 hashes of attachments against list of known malicious hashes.

## Parameters
* md5_hashes (string): name of lexical expression list with malicious MD5 hashes (empty for no check of MD5 hash)
* sha256_hashes (string): name of lexical expression list with malicious SHA-256 hashes (empty for no check of SHA-256 hash)

## Lexical expression lists
* MD5 hashes: list of malicious MD5 hashes
* SHA-256 hashes: list of malicious SHA-256 hashes

## Hold Areas
* Check hash: mails with attachments with malicious hashes
