check_yara.py V1.0.0
====================

Check raw email data (or attachments) against YARA rules.

## Notes
The default setup of the policy rule is for checking raw email data. Alternatively specific media types can be scanned by adjusting the media type filter in the policy rule and removing `-i "%ITEMID%"` from the command line parameters.

## Parameters
* yara_rules (string): name of lexical list with YARA rules

## Hold Areas
* YARA detected: mails matching YARA rule
