check_private.py V7.0.0
=======================

Check sensitivity header for private keyword and that private mails not exceed size limit and have no attachments.

## Parameters
* max_size (integer): maximum mail size for private mails in kB

## Hold Areas
* Not private: mails without sensitivity header or sensitivity header not private
* Invalid private: mails with private sensitivity header but exceeding size limit or having attachments
