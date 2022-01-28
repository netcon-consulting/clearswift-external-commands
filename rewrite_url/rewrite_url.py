# rewrite_url.py V2.1.0
#
# Copyright (c) 2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
from urllib.request import urlopen, Request
from socket import timeout
from bs4 import BeautifulSoup

ADDITIONAL_ARGUMENTS = ( )
CONFIG_PARAMETERS = ( "redirect_list", "timeout", "substitution_list", "annotation_text", "annotation_html" )

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.66 Safari/537.36"

PATTERN_URL = re.compile(r"((?:https?://|www\.|ftp\.)[A-Za-z0-9._~:/?#[\]@!$&'()*+,;%=-]+)", re.IGNORECASE)
PATTERN_STRIP = re.compile(r"^https?://(\S+)$", re.IGNORECASE)

def resolve_redirect(url, request_timeout):
    """
    Resolve redirect URL.

    :type url: str
    :type request_timeout: int
    :rtype: str
    """
    try:
        return urlopen(Request(url, headers={ "User-Agent": USER_AGENT }), timeout=request_timeout).url
    except timeout:
        raise Exception("Timeout redirect '{}'".format(url))
    except Exception:
        raise Exception("Invalid redirect '{}'".format(url))

def modify_text(content, set_redirect, dict_redirect, request_timeout, dict_replace):
    """
    Rewrite URLs in text body.

    :type content: str
    :type set_redirect: set
    :type dict_redirect: dict
    :type request_timeout: int
    :type dict_replace: dict
    :rtype: str or None
    """
    modified = False

    for url in re.findall(PATTERN_URL, content):
        url_original = url

        if set_redirect is not None:
            for pattern in set_redirect:
                if re.search(pattern, url) is not None:
                    if url in dict_redirect:
                        url_redirect = dict_redirect[url]
                    else:
                        url_redirect = resolve_redirect(url, request_timeout)

                        if url_redirect != url:
                            dict_redirect[url] = url_redirect

                    if url_redirect != url:
                        url = url_redirect

                        break

        if dict_replace is not None:
            for (pattern, replace) in dict_replace.items():
                url_replace = re.sub(pattern, replace, url)

                if url_replace != url:
                    url = url_replace

                    break

        if url != url_original:
            content = content.replace(url_original, url)

            modified = True

    if modified:
        return content

    return None

def modify_html(content, charset, set_redirect, dict_redirect, request_timeout, dict_replace):
    """
    Rewrite URLs in html body.

    :type content: str
    :type charset: str
    :type set_redirect: set
    :type dict_redirect: dict
    :type request_timeout: int
    :type dict_replace: dict
    :rtype: str or None
    """
    soup = BeautifulSoup(content, features="html5lib")

    href_modified = False

    for url in { a["href"] for a in soup.findAll("a", href=True) }:
        url_original = url

        if set_redirect is not None:
            for pattern in set_redirect:
                if re.search(pattern, url) is not None:
                    if url in dict_redirect:
                        url_redirect = dict_redirect[url]
                    else:
                        url_redirect = resolve_redirect(url, request_timeout)

                        if url_redirect != url:
                            dict_redirect[url] = url_redirect

                    if url_redirect != url:
                        url = url_redirect

                        break

        if dict_replace is not None:
            for (pattern, replace) in dict_replace.items():
                url_replace = re.sub(pattern, replace, url)

                if url_replace != url:
                    url = url_replace

                    break

        if url != url_original:
            match = re.search(PATTERN_STRIP, url_original)

            if match is None:
                url_strip = None
            else:
                url_strip = match.group(1)

            for a in soup.find_all("a", href=url_original):
                a["href"] = url

                if a.text == url_original or a.text == url_strip:
                    a.string = url

                if a.has_attr("title"):
                    title = a["title"]

                    if title == url_original or title == url_strip:
                        a["title"] = url

            href_modified = True

    if href_modified:
        try:
            content = soup.encode(charset).decode(charset)
        except Exception:
            raise Exception("Error converting soup to string")

    text_modified = False

    for url in re.findall(PATTERN_URL, html2text(content)):
        url_original = url

        if set_redirect is not None:
            for pattern in set_redirect:
                if re.search(pattern, url) is not None:
                    if url in dict_redirect:
                        url_redirect = dict_redirect[url]
                    else:
                        url_redirect = resolve_redirect(url, request_timeout)

                    if url_redirect != url:
                        url = url_redirect

                        break

        if dict_replace is not None:
            for (pattern, replace) in dict_replace.items():
                url_replace = re.sub(pattern, replace, url)

                if url_replace != url:
                    url = url_replace

                    break

        if url != url_original:
            content = content.replace(url_original, url)

            text_modified = True

    if href_modified or text_modified:
        return content

    return None

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
    else:
        set_redirect = None

        dict_redirect = None

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
            dict_replace = { re.compile(substitution.split("\n")[0]): substitution.split("\n")[1] for substitution in set_substitution }
        except Exception:
            write_log(log, "Invalid substitution list")

            return ReturnCode.DETECTED
    else:
        dict_replace = None

    email_modified = False

    try:
        part = extract_part(email, "text/plain")
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    if part is not None:
        (part, charset, content) = part

        try:
            content = modify_text(content, set_redirect, dict_redirect, config.timeout, dict_replace)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        if content is not None:
            if config.annotation_text:
                try:
                    annotation_content = annotation(config.annotation_text).text
                except Exception as ex:
                    write_log(log, ex)

                    return ReturnCode.DETECTED

                content = annotation_content + content

                if charset != CHARSET_UTF8 and not string_ascii(annotation_content):
                    charset = CHARSET_UTF8

            if HEADER_CTE in part:
                del part[HEADER_CTE]

            part.set_payload(content, charset=charset)

            email_modified = True

    try:
        part = extract_part(email, "text/html")
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    if part is not None:
        (part, charset, content) = part

        try:
            content = modify_html(content, charset, set_redirect, dict_redirect, config.timeout, dict_replace)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        if content is not None:
            if config.annotation_html:
                try:
                    annotation_content = annotation(config.annotation_html).html
                except Exception as ex:
                    write_log(log, ex)

                    return ReturnCode.DETECTED

                content = annotate_html(content, annotation_content)

                if charset != CHARSET_UTF8 and not string_ascii(annotation_content):
                    charset = CHARSET_UTF8

            if HEADER_CTE in part:
                del part[HEADER_CTE]

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
