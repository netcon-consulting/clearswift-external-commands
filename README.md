Clearswift external commands
============================

Collection of external commands for Clearswift SEG 5.

## Installation

Installation of external commands recommended with the install script: https://github.com/netcon-consulting/external_commands

## External commands
* check_internal: check whether sender IP is in internal networks and sender domain is internal domain
* check_private: check sensitivity header for private keyword and that private mails not exceed size limit and have no attachments
* check_qr: check URLs from QR-codes in pictures against URL blacklist and corresponding domains against reputation blacklists
* check_rcptlimit: check number of recipients (in to and cc headers) against limit
* check_string: check raw email data for combination of strings
* decrypt_pdf: attempt to decrypt PDF using a provided list of passwords and optionally scan contents with AV and removes encryption
* decrypt_zip: attempt to decrypt ZIP container using a provided list of passwords and optionally scan contents with AV and removes encryption
* dmarc_report: parse DMARC xml reports and write results to syslog
* encrypt_mail: zip-encrypt email if trigger keyword present in subject header and send it to recipients and generated password to sender
* fix_charset: set charset in meta tag in html body to charset defined in content-type header
* replace_url: replace URLs in text and html body if one of the keywords is found
* tag_mail: add and remove tags in address and subject headers, text and html bodies and calendar objects
