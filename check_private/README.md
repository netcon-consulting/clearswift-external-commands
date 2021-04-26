check_private.py V1.2.0
=======================

Check sensitivity header for private keyword and that private mails not exceed size limit and have no attachments.

## Parameters
* max_size_kb (integer): maximum mail size for private mails in kB

## Hold Areas
* Not private: mails without sensitivity header or sensitivity header not private
* Invalid private: mails with private sensitivity header but exceeding size limit or having attachments
