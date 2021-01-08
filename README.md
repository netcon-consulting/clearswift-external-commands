Clearswift external commands
============================

Collection of external commands for Clearswift SEG 5.

## Installation

Installation of external commands recommended with the install script: https://github.com/netcon-consulting/external_commands

## External commands
* check_internal: checks whether sender IP is in internal networks and sender domain is internal domain
* check_private: checks sensitivity header for private keyword and that private mails not exceed size limit and have no attachments
* check_rcptlimit: checks number of recipients (in to and cc headers) against limit
* check_string: checks raw email text for combination of strings
* decrypt_zip: attempts to decrypt zip file using a provided list of passwords and if successful scans contents with Sophos AV
* dmarc_report: parses DMARC xml reports and writes results to syslog
* encrypt_mail: zip-encrypts email if trigger keyword present in subject header and sends it to recipients and generated password to sender
* fix_charset: sets charset in meta tag in html body to charset defined in content-type header
* replace_url: replaces URLs in text and html body if one of the keywords is found
* tag_mail: adds and removes tags in address and subject headers and text and html bodies
