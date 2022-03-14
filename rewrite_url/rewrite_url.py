# rewrite_url.py V3.0.1
#
# Copyright (c) 2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
from urllib.request import urlopen, Request
from socket import timeout
from bs4 import BeautifulSoup

ADDITIONAL_ARGUMENTS = ( )
CONFIG_PARAMETERS = ( "redirect_list", "timeout", "check_redirect", "url_blacklist", "url_whitelist", "substitution_list", "annotation_text", "annotation_html" )

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.66 Safari/537.36"

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

def check_blacklisted(url, set_whitelist, set_blacklist, name_blacklist):
    """
    Check if URL is blacklisted.

    :type url: str
    :type set_blacklist: set
    :type set_whitelist: set
    :type name_blacklist: str
    """
    result = url_blacklisted(url, set_whitelist, set_blacklist)

    if result is not None:
        if result:
            raise Exception("'{}' listed on '{}'".format(result[0], result[1]))

        raise Exception("'{}' listed on '{}'".format(url, name_blacklist))

def modify_text(content, set_redirect, dict_redirect, request_timeout, set_whitelist, set_blacklist, set_clean, name_blacklist, dict_replace):
    """
    Rewrite URLs in text body.

    :type content: str
    :type set_redirect: set
    :type dict_redirect: dict
    :type request_timeout: int
    :type set_whitelist: set
    :type set_blacklist: set
    :type set_clean: set
    :type name_blacklist: str
    :type dict_replace: dict
    :rtype: str or None
    """
    modified = False

    for url in set(re.findall(PATTERN_URL, content)):
        url_original = url

        if set_redirect is not None:
            for pattern in set_redirect:
                if re.search(pattern, url) is not None:
                    if url in dict_redirect:
                        url_redirect = dict_redirect[url]
                    else:
                        url_redirect = resolve_redirect(url, request_timeout)

                        dict_redirect[url] = url_redirect

                    if url_redirect != url:
                        if set_clean is not None and url_redirect not in set_clean:
                            check_blacklisted(url_redirect, set_whitelist, set_blacklist, name_blacklist)

                            set_clean.add(url_redirect)

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

def modify_html(content, charset, set_redirect, dict_redirect, request_timeout, set_whitelist, set_blacklist, set_clean, name_blacklist, dict_replace):
    """
    Rewrite URLs in html body.

    :type content: str
    :type charset: str
    :type set_redirect: set
    :type dict_redirect: dict
    :type request_timeout: int
    :type set_whitelist: set
    :type set_blacklist: set
    :type set_clean: set
    :type name_blacklist: str
    :type dict_replace: dict
    :rtype: str or None
    """
    soup = BeautifulSoup(content, features="html5lib")

    html_modified = False

    for url in { a["href"] for a in soup.findAll("a", href=True) }:
        url_original = url

        if set_redirect is not None:
            for pattern in set_redirect:
                if re.search(pattern, url) is not None:
                    if url in dict_redirect:
                        url_redirect = dict_redirect[url]
                    else:
                        url_redirect = resolve_redirect(url, request_timeout)

                        dict_redirect[url] = url_redirect

                    if url_redirect != url:
                        if set_clean is not None and url_redirect not in set_clean:
                            check_blacklisted(url_redirect, set_whitelist, set_blacklist, name_blacklist)

                            set_clean.add(url_redirect)

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
                    a.string.replace_with(url)

                if a.has_attr("title"):
                    title = a["title"]

                    if title == url_original or title == url_strip:
                        a["title"] = url

            html_modified = True

    if html_modified:
        try:
            content = soup.encode(charset).decode(charset)
        except Exception:
            raise Exception("Error converting soup to string")

    text_modified = False

    for url in set(re.findall(PATTERN_URL, html2text(content))):
        url_original = url

        if set_redirect is not None:
            for pattern in set_redirect:
                if re.search(pattern, url) is not None:
                    if url in dict_redirect:
                        url_redirect = dict_redirect[url]
                    else:
                        url_redirect = resolve_redirect(url, request_timeout)

                        dict_redirect[url] = url_redirect

                    if url_redirect != url:
                        if set_clean is not None and url_redirect not in set_clean:
                            check_blacklisted(url_redirect, set_whitelist, set_blacklist, name_blacklist)

                            set_clean.add(url_redirect)

                        url = url_redirect

                        break

        if dict_replace is not None:
            for (pattern, replace) in dict_replace.items():
                url_replace = re.sub(pattern, replace, url)

                if url_replace != url:
                    url = url_replace

                    break

        if url != url_original:
            for tag in soup.findAll(text=re.compile(url_original)):
                tag.string.replace_with(tag.text.replace(url_original, url))

            text_modified = True

    if text_modified:
        try:
            content = soup.encode(charset).decode(charset)
        except Exception:
            raise Exception("Error converting soup to string")

    if html_modified or text_modified:
        return content

    return None

def run_command(input, log, config, additional):
    """
    Rewrite URLs in text and html body by resolving redirects (and optionally check if resolved URL is blacklisted) and replacing URL parts.

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

        if config.check_redirect:
            if config.url_blacklist:
                try:
                    set_blacklist = set(url_list(config.url_blacklist))
                except Exception as ex:
                    write_log(log, ex)

                    return ReturnCode.ERROR

                set_blacklist = { re.compile(url2regex(url), re.IGNORECASE) for url in set_blacklist }
            else:
                set_blacklist = None

            if config.url_whitelist:
                try:
                    set_whitelist = set(url_list(config.url_whitelist))
                except Exception as ex:
                    write_log(log, ex)

                    return ReturnCode.ERROR

                set_whitelist = { re.compile(url2regex(url), re.IGNORECASE) for url in set_whitelist }
            else:
                set_whitelist = None

            set_clean = set()
        else:
            set_blacklist = None
            set_whitelist = None
            set_clean = None
    else:
        set_redirect = None
        dict_redirect = None
        set_blacklist = None
        set_whitelist = None
        set_clean = None

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
            content = modify_text(content, set_redirect, dict_redirect, config.timeout, set_whitelist, set_blacklist, set_clean, config.url_blacklist, dict_replace)
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
            content = modify_html(content, charset, set_redirect, dict_redirect, config.timeout, set_whitelist, set_blacklist, set_clean, config.url_blacklist, dict_replace)
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
