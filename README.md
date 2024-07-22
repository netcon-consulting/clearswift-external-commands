Clearswift external commands
============================

Collection of external commands for Clearswift SEG 5.

## Dependencies

* [toml](https://pypi.org/project/toml/)
* [pyzipper](https://pypi.org/project/pyzipper/)
* [lxml](https://pypi.org/project/lxml/)
* [html5lib](https://pypi.org/project/html5lib/)
* [dnspython](https://pypi.org/project/dnspython/)
* [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
* [faust-cchardet](https://pypi.org/project/faust-cchardet/)

## Installation

Installation of external commands recommended with the install script: https://github.com/netcon-consulting/external_commands

## External commands
* add_tag: add tags in address and subject headers, text and HTML bodies and calendar objects
* check_condition: check custom condition
* check_hash: check MD5 and SHA-256 hashes of attachments against list of known malicious hashes
* check_internal: check whether sender IP is in internal networks and sender domain is internal domain
* check_ocr: check text in pictures against regular expression blacklist
* check_private: check sensitivity header for private keyword and that private mails not exceed size limit and have no attachments
* check_qr: check URLs from QR-codes in pictures against URL blacklist and corresponding domains against reputation blacklists
* check_rcptlimit: check number of recipients (in To and Cc headers) against limit
* check_string: check raw email data for combination of strings
* check_yara: check raw email data (or attachments) against YARA rules
* clean_mail: clean regular expressions and annotations from text and HTML mail bodies
* decrypt_pdf: attempt to decrypt PDF using a provided list of passwords and optionally scan contents with AV and removes encryption
* decrypt_zip: attempt to decrypt ZIP container using a provided list of passwords and optionally scan contents with AV and removes encryption
* dkim_header: add header with result of SpamLogic DKIM check
* dmarc_report: parse DMARC XML reports and write results to syslog
* encrypt_mail: zip-encrypt email if trigger keyword present in subject header and send it to recipients and generated password to sender
* fix_charset: set charset in meta tag in HTML body to charset defined in content-type header
* remove_tag: remove tags in address and subject headers, text and HTML bodies and calendar objects
* replace_url: replace URLs in text and HTML body if one of the keywords is found
* rewrite_url: rewrite URLs in text and HTML body by resolving redirects (and optionally check if resolved URL is blacklisted) and replacing URL parts
