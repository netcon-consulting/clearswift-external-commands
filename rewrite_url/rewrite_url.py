# rewrite_url.py V8.0.0
#
# Copyright (c) 2022-2023 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import re
from urllib.request import urlopen, Request
from urllib.parse import quote
from socket import timeout
from bs4 import BeautifulSoup

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = True
CONFIG_PARAMETERS = ( "exception_list", "redirect_list", "timeout", "check_redirect", "url_blacklist", "url_whitelist", "substitution_list", "token_list", "annotation_text", "annotation_html" )

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.66 Safari/537.36"

PATTERN_STRIP = re.compile(r"^https?://(\S+)$", re.IGNORECASE)

TEMPLATE_TOKEN = "${}"

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

def modify_url(url, set_redirect, request_timeout, set_whitelist, set_blacklist, set_checked, name_blacklist, dict_replace):
    """
    Modify URL.

    :type url: str
    :type dict_modified: dict
    :type set_redirect: set
    :type request_timeout: int
    :type set_whitelist: set
    :type set_blacklist: set
    :type set_checked: set
    :type name_blacklist: str
    :type dict_replace: dict
    :rtype: str
    """
    if set_redirect is not None:
        for pattern in set_redirect:
            if re.search(pattern, url) is not None:
                url_redirect = resolve_redirect(url, request_timeout)

                if url_redirect != url:
                    if set_checked is not None and url_redirect not in set_checked:
                        check_blacklisted(url_redirect, set_whitelist, set_blacklist, name_blacklist)

                        set_checked.add(url_redirect)

                    url = url_redirect

                    break

    if dict_replace is not None:
        for (pattern, replace) in dict_replace.items():
            url_replace = re.sub(pattern, replace, url)

            if url_replace != url:
                url = url_replace

                break

    return url

def modify_text(content, set_exception, dict_modified, set_redirect, request_timeout, set_whitelist, set_blacklist, set_checked, name_blacklist, dict_replace):
    """
    Rewrite URLs in text body.

    :type content: str
    :type set_exception: set
    :type dict_modified: dict
    :type set_redirect: set
    :type request_timeout: int
    :type set_whitelist: set
    :type set_blacklist: set
    :type set_checked: set
    :type name_blacklist: str
    :type dict_replace: dict
    :rtype: str or None
    """
    dict_url = dict()

    for url in set(re.findall(PATTERN_URL, content)):
        for pattern in set_exception:
            if re.search(pattern, url) is not None:
                break
        else:
            if url in dict_modified:
                dict_url[url] = dict_modified[url]
            else:
                url_modified = modify_url(url, set_redirect, request_timeout, set_whitelist, set_blacklist, set_checked, name_blacklist, dict_replace)

                if url_modified != url:
                    dict_modified[url] = url_modified

                    dict_url[url] = url_modified

    if dict_url:
        index_shift = 0

        for match in re.finditer(PATTERN_URL, content):
            url = match.group()

            if url in dict_url:
                url_modified = dict_url[url]

                content = content[:match.start() + index_shift] + url_modified + content[match.end() + index_shift:]

                index_shift += len(url_modified) - len(url)

        return content

    return None

def modify_html(content, charset, set_exception, dict_modified, set_redirect, request_timeout, set_whitelist, set_blacklist, set_checked, name_blacklist, dict_replace):
    """
    Rewrite URLs in HTML body.

    :type content: str
    :type charset: str
    :type set_exception: set
    :type dict_modified: dict
    :type set_redirect: set
    :type request_timeout: int
    :type set_whitelist: set
    :type set_blacklist: set
    :type set_checked: set
    :type name_blacklist: str
    :type dict_replace: dict
    :rtype: str or None
    """
    soup = BeautifulSoup(content, features="html5lib")

    content_modified = False

    for url in { a["href"] for a in soup.findAll("a", href=re.compile(r"^(?!mailto:).+", re.IGNORECASE)) }:
        for pattern in set_exception:
            if re.search(pattern, url) is not None:
                break
        else:
            modified = False

            if url in dict_modified:
                url_modified = dict_modified[url]

                modified = True
            else:
                url_modified = modify_url(url, set_redirect, request_timeout, set_whitelist, set_blacklist, set_checked, name_blacklist, dict_replace)

                if url_modified != url:
                    dict_modified[url] = url_modified

                    modified = True

            if modified:
                match = re.search(PATTERN_STRIP, url)

                if match is None:
                    url_strip = None
                else:
                    url_strip = match.group(1)

                for a in soup.find_all("a", href=url):
                    a["href"] = url_modified

                    if a.text == url:
                        a.find(text=url).replace_with(url_modified)
                    elif a.text == url_strip:
                        a.find(text=url_strip).replace_with(url_modified)

                    if a.has_attr("title"):
                        title = a["title"]

                        if title == url or title == url_strip:
                            a["title"] = url_modified

                content_modified = True

    if content_modified:
        try:
            content = soup.encode(charset).decode(charset)
        except Exception:
            raise Exception("Error converting soup to string")

    dict_url = dict()

    for url in set(re.findall(PATTERN_URL, extract_text(content))):
        for pattern in set_exception:
            if re.search(pattern, url) is not None:
                break
        else:
            if url in dict_modified:
                dict_url[url] = dict_modified[url]
            else:
                url_modified = modify_url(url, set_redirect, request_timeout, set_whitelist, set_blacklist, set_checked, name_blacklist, dict_replace)

                if url_modified != url:
                    dict_modified[url] = url_modified

                    dict_url[url] = url_modified

    if dict_url:
        for string in soup.findAll(text=PATTERN_URL):
            text = string.text

            index_shift = 0

            for match in re.finditer(PATTERN_URL, text):
                url = match.group()

                if url in dict_url:
                    url_modified = dict_url[url]

                    text = text[:match.start() + index_shift] + url_modified + text[match.end() + index_shift:]

                    index_shift += len(url_modified) - len(url)

            string.replace_with(text)

        try:
            content = soup.encode(charset).decode(charset)
        except Exception:
            raise Exception("Error converting soup to string")

        content_modified = True

    if content_modified:
        return content

    return None

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Rewrite URLs in text and HTML body by resolving redirects (and optionally check if resolved URL is blacklisted) and replacing URL parts.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    :type disable_splitting: bool
    :type reformat_header: bool
    """
    if not (config.redirect_list or config.substitution_list):
        return ReturnCode.NONE

    try:
        email = read_email(input, disable_splitting)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.DETECTED

    if config.exception_list:
        try:
            set_exception = set(url_list(config.exception_list))
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.ERROR

        set_exception = { re.compile(url2regex(url), re.IGNORECASE) for url in set_exception }
    else:
        set_exception = set()

    dict_modified = dict()

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

            set_checked = set()
        else:
            set_blacklist = None
            set_whitelist = None
            set_checked = None
    else:
        set_redirect = None
        set_blacklist = None
        set_whitelist = None
        set_checked = None

    if config.substitution_list:
        try:
            set_substitution = set(lexical_list(config.substitution_list))
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

        if config.token_list:
            try:
                set_token = set(lexical_list(config.token_list))
            except Exception as ex:
                write_log(log, ex)

                return ReturnCode.DETECTED

            if not set_token:
                write_log(log, "Token list is empty")

                return ReturnCode.DETECTED

            tokens_missing = set_token - optional.keys()

            if tokens_missing:
                write_log(log, "Missing optional arguments for tokens {}".format(str(tokens_missing)[1:-1]))

                return ReturnCode.DETECTED

            dict_token = { token: optional[token] for token in set_token }

            for (pattern, replace) in dict_replace.items():
                modified = False

                for (token, value) in dict_token.items():
                    token = TEMPLATE_TOKEN.format(token)

                    if token in replace:
                        replace = replace.replace(token, quote(value))

                        modified = True

                if modified:
                    dict_replace[pattern] = replace
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
            content = modify_text(content, set_exception, dict_modified, set_redirect, config.timeout, set_whitelist, set_blacklist, set_checked, config.url_blacklist, dict_replace)
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
            content = modify_html(content, charset, set_exception, dict_modified, set_redirect, config.timeout, set_whitelist, set_blacklist, set_checked, config.url_blacklist, dict_replace)
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
            write_email(email, input, reformat_header)
        except Exception as ex:
            write_log(log, ex)

            return ReturnCode.DETECTED

        return ReturnCode.MODIFIED

    return ReturnCode.NONE
