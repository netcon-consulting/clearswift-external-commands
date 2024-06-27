check_ocr.py V3.1.0
===================

Check text in pictures against regular expression blacklist.

## Parameters
* regex_blacklist (string): name of lexical list with blacklisted regex
* regex_whitelist (string): name of lexical list with whitelisted regex (empty for no whitelist)
* size_min (integer): minimum image size in pixel
* size_max (integer): maximum image size in pixel
* skip_unsupported (boolean): skip unsupported image format/type

## Lexical lists
* Regex blacklist: Regex blacklist
* Regex whitelist: Regex whitelist

## Hold Areas
* Check OCR: mails with pictures containing blacklisted regex
