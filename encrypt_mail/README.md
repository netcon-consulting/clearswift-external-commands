encrypt_mail.py V3.0.0
======================

Zip-encrypt email if trigger keyword present in subject header and send it to recipients and generated password to sender.

## Parameters
* keyword_encryption (string): trigger keyword in subject header
* password_length (integer): length of zip-encryption password
* password_punctuation (boolean): include punctuation characters for password generation

## Hold Areas
* Encrypt mail: copies of the original mails which have been encrypted
