check_custom.py V2.0.0
======================

Check email with configurable custom function.

## Parameters
* name_expression_list (string): name of lexical expression list with check function

## Lexical expression lists
* Check custom function: list with one item holding Python3 code defining custom function 'check_email'

## Notes
The custom function 'check_mail' needs to return the appropriate return code `ReturnCode.NOT_DETECTED`, `ReturnCode.DETECTED` or `ReturnCode.ERROR`. Also for `ReturnCode.DETECTED` and `ReturnCode.ERROR` a corresponding message should be written to the log using the `write_log` function.

Example:
```
import re

def check_email(email, log):
    """
    Detect emails from IP 1.2.3.4 with subject header not matching regex '^Invoice \d{10}$'
    """

    if "Received" in email:
        header_received = email.get("Received").replace("\n", "")

        match = re.search(r"from \S+ \(\S+ \[([^]]+)\]\)", header_received)

        if match is not None:
            if match.group(1) == "195.201.219.214":
                if "Subject" in email:
                    header_subject = str(email.get("Subject")).replace("\n", "").strip()

                    if re.search(r"^Invoice \d{10}$", header_subject) is None:
                        write_log(log, "Invalid subject header")

                        return ReturnCode.DETECTED
                else:
                    write_log(log, "No subject header")

                    return ReturnCode.DETECTED

    return ReturnCode.NOT_DETECTED
```
