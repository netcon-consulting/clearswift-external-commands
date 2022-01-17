# rewrite_url.py V1.0.0
#
# Copyright (c) 2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
from urllib.request import urlopen
from socket import timeout
from bs4 import BeautifulSoup

ADDITIONAL_ARGUMENTS = ( )
CONFIG_PARAMETERS = ( "redirect_list", "timeout", "substitution_list" )

PATTERN_URL = re.compile(r"((?:https?://|www\.|ftp\.)[A-Za-z0-9._~:/?#[\]@!$&'()*+,;%=-]+)", re.IGNORECASE)

def run_command(input, log, config, additional):
    """
    Rewrite URLs in text and html body by resolving redirects and replacing URL parts.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    """
    if not (config.redirect_list or config.substitution_list):
        return ReturnCode.NONE

    try:
        email = read_email(input)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    if config.redirect_list:
        try:
            set_redirect = set(url_list(config.redirect_list))
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        if not set_redirect:
            write_log(log, "Redirect list is empty")

            return ReturnCode.DETECTED

        set_redirect = { re.compile(url2regex(url), re.IGNORECASE) for url in set_redirect }

        dict_redirect = dict()

    if config.substitution_list:
        try:
            set_substitution = (lexical_list(config.substitution_list))
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        if not set_substitution:
            write_log(log, "Substitution list is empty")

            return ReturnCode.DETECTED

        try:
            dict_replace = { substitution.split("\n")[0]: substitution.split("\n")[1] for substitution in set_substitution }
        except Exception:
            write_log(log, "Invalid substitution list")

            return ReturnCode.DETECTED

    email_modified = False

    try:
        part = extract_part(email, "text/plain")
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    if part is not None:
        (part, charset, content) = part

        body_modified = False

        for url in { match.group(1) for match in re.findall(PATTERN_URL, content) }
            url_original = url

            if config.redirect_list:
                for pattern in set_redirect:
                    if re.search(pattern, url) is not None:
                        try:
                            url_redirect = urlopen(url, timeout=config.timeout).url
                        except timeout:
                            write_log(log, "Timeout redirect '{}'".format(url))

                            return ReturnCode.DETECTED
                        except Exception:
                            write_log(log, "Invalid redirect '{}'".format(url))

                            return ReturnCode.DETECTED

                        if url_redirect != url:
                            dict_redirect[url] = url_redirect

                            url = url_redirect

                            break

            if config.substitution_list:
                for (pattern, replace) in dict_replace.items():
                    url_replace = re.sub(pattern, replace, url)
                    
                    if url_replace != url:
                        url = url_replace

                        break

            if url != url_original:
                content = content.replace(url_original, url)

                body_modified = True

        if body_modified:
            part.set_payload(content, charset=charset)

            email_modified = True

    try:
        part = extract_part(email, "text/html")
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    if part is not None:
        (part, charset, content) = part

        body_modified = False

        soup = BeautifulSoup(content, features="html5lib")

        for url in { a["href"] for a in soup.findAll("a", href=True) }:
            url_original = url
            
            if config.redirect_list:
                for pattern in set_redirect:
                    if re.search(pattern, url) is not None:
                        if config.redirect_list and url in dict_redirect:
                            url_redirect = dict_redirect[url]
                        else:
                            try:
                                url_redirect = urlopen(url, timeout=config.timeout).url
                            except timeout:
                                write_log(log, "Timeout redirect '{}'".format(url))

                                return ReturnCode.DETECTED
                            except Exception:
                                write_log(log, "Invalid redirect '{}'".format(url))

                                return ReturnCode.DETECTED

                        if url_redirect != url:
                            url = url_redirect

                            break

            if config.substitution_list:
                for (pattern, replace) in dict_replace.items():
                    url_replace = re.sub(pattern, replace, url)
                    
                    if url_replace != url:
                        url = url_replace

                        break

            if url != url_original:
                for a in soup.find_all("a", href=url_original):
                    a["href"] = url

                body_modified = True

        if body_modified:
            try:
                content = soup.encode(charset).decode(charset)
            except Exception:
                write_log(log, "Error converting soup to string")

                return ReturnCode.DETECTED

            part.set_payload(content, charset=charset)

            email_modified = True

    if email_modified:
        try:
            with open(input, "wb") as f:
                f.write(email.as_bytes())
        except Exception:
            write_log(log, "Error writing '{}'".format(input))

            return ReturnCode.DETECTED

        return ReturnCode.MODIFIED

    return ReturnCode.NONE
