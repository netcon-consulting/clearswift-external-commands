# command_library.py V11.3.0
#
# Copyright (c) 2020-2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

"""
Collection of functions for Clearswift external commands.
"""

from sys import maxsize
from collections import namedtuple
from email import message_from_binary_file, errors
from email.policy import EmailPolicy
from email.headerregistry import HeaderRegistry, BaseHeader, MessageIDHeader
from email._header_value_parser import _steal_trailing_WSP_if_exists, _fold_as_ew, quote_string, get_dot_atom_text, get_word, get_cfws, get_no_fold_literal, get_domain, get_unstructured, TokenList, Terminal, HeaderLabel, ValueTerminal, CFWSList, WhiteSpaceTerminal, MessageID, MsgID, ObsLocalPart, InvalidMessageID, CFWS_LEADER, PHRASE_ENDS, DOT, SPECIALS, WSP
from email.utils import _has_surrogates
from xml.sax import make_parser, handler
from io import BytesIO
from re import compile, search, escape, sub, IGNORECASE
from subprocess import run, PIPE, DEVNULL
from socket import socket, AF_INET, SOCK_STREAM
from urllib.parse import quote, unquote
from pyzipper import AESZipFile, ZIP_LZMA
from lxml.html.html5parser import etree
from dns.resolver import resolve

CHARSET_UTF8 = "utf-8"

HEADER_CTE = "Content-Transfer-Encoding"

BUFFER_TCP = 4096 # in bytes

PATTERN_URL = compile(r"((?:https?://|www\.|ftp\.)[A-Za-z0-9._-]+[A-Za-z0-9](?:/[A-Za-z0-9._~:/?#[\]@!$&'()*+,;%=-]*[A-Za-z0-9_~/#[\]@$&()*+%=-])?)", IGNORECASE)
PATTERN_PROTOCOL = compile(r"^(https?://)(\S+)$", IGNORECASE)
PATTERN_DOMAIN = compile(r"^(?:https?://)?([^/]+)", IGNORECASE)

TupleReputation = namedtuple("TupleReputation", "query_domain record_type match")

LIST_REPUTATION = [
    TupleReputation(query_domain="dnsbl7.mailshell.net", record_type="A", match=compile(r"^((25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.){3}(((?!100|101)[0-9])+)$")),
    TupleReputation(query_domain="multi.surbl.org", record_type="TXT", match=compile(r"^(((?!Query Refused).)+)$")),
    TupleReputation(query_domain="multi.uribl.com", record_type="TXT", match=compile(r"^(((?!Query Refused).)+)$")),
]

CHARSET_EQUIVALENT = {
    "windows-31j": "cp932",
    "windows-874": "cp874",
    "big-5": "big5",
    "8859_1": "iso-8859-1",
}

LIST_ADDRESS = "address"
LIST_CONNECTION = "connection"
LIST_FILENAME = "filename"
LIST_URL = "url"
LIST_LEXICAL = "lexical"

TupleInfo = namedtuple("TupleInfo", "tag_attribute tag_table tag_list tag_item")

LIST_INFO = {
    LIST_ADDRESS: TupleInfo(tag_attribute=None, tag_table="AddressListTable", tag_list="AddressList", tag_item="Address"),
    LIST_CONNECTION: TupleInfo(tag_attribute=None, tag_table="TLSEndPointCollection", tag_list="TLSEndPoint", tag_item="Host"),
    LIST_FILENAME: TupleInfo(tag_attribute=None, tag_table="FilenameListTable", tag_list="FilenameList", tag_item="Filename"),
    LIST_URL: TupleInfo(tag_attribute=None, tag_table="UrlListTable", tag_list="UrlList", tag_item="Url"),
    LIST_LEXICAL: TupleInfo(tag_attribute="text", tag_table="TextualAnalysisCollection", tag_list="TextualAnalysis", tag_item="Phrase")
}

TupleAnnotation = namedtuple("TupleAnnotation", "text html")

TYPE_TEXT = "text/plain"
TYPE_HTML = "text/html"
TYPE_CALENDAR = "text/calendar"

class HandlerValue(HandlerBase):
    """
    Custom content handler for lists stored in tag values.
    """
    def __init__(self, tag_table, tag_list, tag_item, regex_list, regex_item):
        """
        :type tag_table: str
        :type tag_list: str
        :type tag_item: str
        :type regex_list: str
        :type regex_item: str
        """
        self.name_list = None
        self.item = None

        super().__init__(tag_table, tag_list, tag_item, regex_list, regex_item)

    def startElement(self, name, attrs):
        if self.name_list is not None and name == self.tag_item:
            self.item = ""
        elif name == self.tag_list and "name" in attrs:
            name_list = attrs["name"]

            if search(self.pattern_list, name_list):
                self.name_list = name_list

                self.list_item = list()

    def characters(self, content):
        if self.item is not None:
            self.item += content

    def endElement(self, name):
        if self.name_list is not None and name == self.tag_item and search(self.pattern_item, self.item):
                self.list_item.append(self.item)

                self.item = None
        elif name == self.tag_list and self.name_list is not None:
            if self.list_item:
                self.list_itemlist.append(( self.name_list, self.list_item ))

            self.name_list = None
        elif name == self.tag_table:
            raise SAXExceptionFinished

class HandlerAnnotation(handler.ContentHandler):
    """
    Custom content handler for annotations.
    """
    def __init__(self, regex_annotation):
        """
        :type regex_item: str
        """
        self.pattern_annotation = compile(regex_annotation)
        self.list_annotation = list()
        self.name_annotation = None
        self.text = None
        self.html = None

        super().__init__()

    def startElement(self, name, attrs):
        if self.name_annotation is not None and name == "Plain":
            self.text = ""
        elif self.name_annotation is not None and name == "Html":
            self.html = ""
        elif name == "Annotation" and "name" in attrs:
            name_annotation = attrs["name"]

            if search(self.pattern_annotation, name_annotation):
                self.name_annotation = name_annotation

    def characters(self, content):
        if self.text is not None:
            self.text += content
        elif self.html is not None:
            self.html += content

    def endElement(self, name):
        if self.name_annotation is not None and name == "Plain":
            self.annotation_text = unquote(self.text.replace("+", " "))

            self.text = None
        elif self.name_annotation is not None and name == "Html":
            self.annotation_html = self.html

            self.html = None
        elif name == "Annotation" and self.name_annotation is not None:
            self.list_annotation.append(TupleAnnotation(text=self.annotation_text, html=self.annotation_html))

            self.name_annotation = None
        elif name == "AnnotationCollection":
            raise SAXExceptionFinished

    def getAnnotations(self):
        """
        Return list of annotations.

        :rtype: list
        """
        return self.list_annotation

class EmailPolicyCustom(EmailPolicy):
    disable_splitting = False

class Header(TokenList):
    token_type = "header"

    def fold(self, *, policy):
        maxlen = policy.max_line_length or maxsize

        if policy.utf8:
            encoding = "utf-8"
        else:
            encoding = "us-ascii"

        lines = [""]

        leading_whitespace = ""

        last_ew = None

        last_charset = None

        wrap_as_ew_blocked = 0

        want_encoding = False

        end_ew_not_allowed = Terminal("", "wrap_as_ew_blocked")

        parts = list(self)

        while parts:
            part = parts.pop(0)

            if part is end_ew_not_allowed:
                wrap_as_ew_blocked -= 1

                continue

            tstr = str(part)

            if part.token_type == "ptext" and set(tstr) & SPECIALS:
                want_encoding = True

            try:
                tstr.encode(encoding)

                charset = encoding
            except UnicodeEncodeError:
                if any(isinstance(x, errors.UndecodableBytesDefect) for x in part.all_defects):
                    charset = "unknown-8bit"
                else:
                    charset = "utf-8"

                want_encoding = True

            if part.token_type == "mime-parameters":
                fold_mime_parameters(part, lines, maxlen, encoding, policy.disable_splitting)

                continue

            if want_encoding and not wrap_as_ew_blocked:
                if not part.as_ew_allowed:
                    want_encoding = False

                    last_ew = None

                    if part.syntactic_break:
                        encoded_part = part.fold(policy=policy)[:-len(policy.linesep)]

                        if policy.linesep not in encoded_part:
                            if len(encoded_part) > maxlen - len(lines[-1]):
                                newline = _steal_trailing_WSP_if_exists(lines)

                                lines.append(newline)

                            lines[-1] += encoded_part

                            continue

                if not hasattr(part, "encode"):
                    parts = list(part) + parts

                    want_encoding = False

                    continue
                elif part.as_ew_allowed:
                    if (last_ew is not None and charset != last_charset and (last_charset == "unknown-8bit" or last_charset == "utf-8" and charset != "us-ascii")):
                        last_ew = None

                    last_ew = _fold_as_ew(tstr, lines, maxlen, last_ew, part.ew_combine_allowed, charset, leading_whitespace)

                    leading_whitespace = ""

                    last_charset = charset

                    want_encoding = False

                    continue
                else:
                    last_ew = None

                    want_encoding = False

            if len(tstr) <= maxlen - len(lines[-1]):
                lines[-1] += tstr

                continue

            leading_whitespace = ""

            if (part.syntactic_break and len(tstr) + 1 <= maxlen):
                newline = _steal_trailing_WSP_if_exists(lines)

                if newline or part.startswith_fws():
                    lines.append(newline + tstr)

                    whitespace_accumulator = []

                    for char in lines[-1]:
                        if char not in WSP:
                            break

                        whitespace_accumulator.append(char)

                    leading_whitespace = "".join(whitespace_accumulator)

                    last_ew = None

                    continue

            if not hasattr(part, "encode"):
                newparts = list(part)

                if not part.as_ew_allowed:
                    wrap_as_ew_blocked += 1

                    newparts.append(end_ew_not_allowed)

                parts = newparts + parts

                continue

            if part.as_ew_allowed and not wrap_as_ew_blocked:
                parts.insert(0, part)

                want_encoding = True

                continue

            newline = _steal_trailing_WSP_if_exists(lines)

            if newline or part.startswith_fws():
                lines.append(newline + tstr)
            else:
                lines[-1] += tstr

        return policy.linesep.join(lines) + policy.linesep

class BaseHeaderCustom(BaseHeader):
    def fold(self, *, policy):
        header = Header([ HeaderLabel([ ValueTerminal(self.name, "header-name"), ValueTerminal(":", "header-sep") ]), ])

        if self._parse_tree:
            header.append(CFWSList([ WhiteSpaceTerminal(" ", "fws") ]))

        header.append(self._parse_tree)

        return header.fold(policy=policy)

def fold_mime_parameters(part, lines, maxlen, encoding, disable_splitting):
    for name, value in part.params:
        if not lines[-1].rstrip().endswith(";"):
            lines[-1] += ";"

        charset = encoding

        error_handler = "strict"

        try:
            value.encode(encoding)

            encoding_required = False
        except UnicodeEncodeError:
            encoding_required = True

            if _has_surrogates(value):
                charset = "unknown-8bit"

                error_handler = "surrogateescape"
            else:
                charset = "utf-8"

        if encoding_required:
            encoded_value = quote(value, safe="", errors=error_handler)

            tstr = "{}*={}''{}".format(name, charset, encoded_value)
        else:
            tstr = "{}={}".format(name, quote_string(value))

        if len(lines[-1]) + len(tstr) + 1 < maxlen:
            lines[-1] = lines[-1] + " " + tstr

            continue
        elif disable_splitting or len(tstr) + 2 <= maxlen:
            lines.append(" " + tstr)

            continue

        section = 0

        extra_chrome = charset + "''"

        while value:
            chrome_len = len(name) + len(str(section)) + 3 + len(extra_chrome)

            if maxlen <= chrome_len + 3:
                maxlen = 78

            splitpoint = maxchars = maxlen - chrome_len - 2

            while True:
                partial = value[:splitpoint]

                encoded_value = quote(partial, safe="", errors=error_handler)

                if len(encoded_value) <= maxchars:
                    break

                splitpoint -= 1

            lines.append(" {}*{}*={}{}".format(name, section, extra_chrome, encoded_value))

            extra_chrome = ""

            section += 1

            value = value[splitpoint:]

            if value:
                lines[-1] += ";"

def get_obs_local_part(value):
    obs_local_part = ObsLocalPart()

    last_non_ws_was_dot = False

    while value and (value[0] == "\\" or value[0] == "[" or value[0] not in PHRASE_ENDS):
        if value[0] == ".":
            if last_non_ws_was_dot:
                obs_local_part.defects.append(errors.InvalidHeaderDefect("invalid repeated '.'"))

            obs_local_part.append(DOT)

            last_non_ws_was_dot = True

            value = value[1:]

            continue
        elif value[0] == "\\":
            obs_local_part.append(ValueTerminal(value[0], "misplaced-special"))

            value = value[1:]

            obs_local_part.defects.append(errors.InvalidHeaderDefect("'\\' character outside of quoted-string/ccontent"))

            last_non_ws_was_dot = False

            continue
        elif value[0] == "[":
            value = value[1:]

            obs_local_part.defects.append(errors.InvalidHeaderDefect("'[' character in local part"))

            last_non_ws_was_dot = False

            continue

        if obs_local_part and obs_local_part[-1].token_type != "dot":
            obs_local_part.defects.append(errors.InvalidHeaderDefect("missing '.' between words"))

        try:
            (token, value) = get_word(value)

            last_non_ws_was_dot = False
        except errors.HeaderParseError:
            if value[0] not in CFWS_LEADER:
                raise

            (token, value) = get_cfws(value)

        obs_local_part.append(token)

    if not obs_local_part:
        raise errors.HeaderParseError("expected obs-local-part but found '{}'".format(value))

    if (obs_local_part[0].token_type == "dot" or obs_local_part[0].token_type == "cfws" and len(obs_local_part) > 1 and obs_local_part[1].token_type == "dot"):
        obs_local_part.defects.append(errors.InvalidHeaderDefect("Invalid leading '.' in local part"))

    if (obs_local_part[-1].token_type == "dot" or obs_local_part[-1].token_type == "cfws" and len(obs_local_part) > 1 and obs_local_part[-2].token_type == "dot"):
        obs_local_part.defects.append(errors.InvalidHeaderDefect("Invalid trailing '.' in local part"))

    if obs_local_part.defects:
        obs_local_part.token_type = "invalid-obs-local-part"

    return ( obs_local_part, value )

def get_msg_id(value):
    msg_id = MsgID()

    if value and value[0] in CFWS_LEADER:
        (token, value) = get_cfws(value)

        msg_id.append(token)

    if not value or value[0] != "<":
        raise errors.HeaderParseError("expected msg-id but found '{}'".format(value))

    msg_id.append(ValueTerminal('<', 'msg-id-start'))

    value = value[1:]

    if value and value[0] == ">":
        msg_id.defects.append(errors.InvalidHeaderDefect("empty msg-id"))

        msg_id.append(ValueTerminal(">", "msg-id-end"))

        value = value[1:]

        return ( msg_id, value )

    try:
        (token, value) = get_dot_atom_text(value)
    except errors.HeaderParseError:
        try:
            (token, value) = get_obs_local_part(value)

            msg_id.defects.append(errors.ObsoleteHeaderDefect("obsolete id-left in msg-id"))
        except errors.HeaderParseError:
            raise errors.HeaderParseError("expected dot-atom-text or obs-id-left but found '{}'".format(value))

    msg_id.append(token)

    if not value or value[0] != "@":
        msg_id.defects.append(errors.InvalidHeaderDefect("msg-id with no id-right"))

        if value and value[0] == ">":
            msg_id.append(ValueTerminal(">", "msg-id-end"))

            value = value[1:]

        return ( msg_id, value )

    msg_id.append(ValueTerminal('@', 'address-at-symbol'))

    value = value[1:]

    try:
        (token, value) = get_dot_atom_text(value)
    except errors.HeaderParseError:
        try:
            (token, value) = get_no_fold_literal(value)
        except errors.HeaderParseError:
            try:
                (token, value) = get_domain(value)

                msg_id.defects.append(errors.ObsoleteHeaderDefect("obsolete id-right in msg-id"))
            except errors.HeaderParseError:
                raise errors.HeaderParseError("expected dot-atom-text, no-fold-literal or obs-id-right but found '{}'".format(value))

    msg_id.append(token)

    if value and value[0] == ">":
        value = value[1:]
    else:
        msg_id.defects.append(errors.InvalidHeaderDefect("missing trailing '>' on msg-id"))

    msg_id.append(ValueTerminal('>', 'msg-id-end'))

    if value and value[0] in CFWS_LEADER:
        (token, value) = get_cfws(value)

        msg_id.append(token)

    return ( msg_id, value )

def parse_message_id(value):
    message_id = MessageID()

    try:
        (token, value) = get_msg_id(value)

        message_id.append(token)
    except errors.HeaderParseError as ex:
        token = get_unstructured(value)

        message_id = InvalidMessageID(token)

        message_id.defects.append(errors.InvalidHeaderDefect("Invalid msg-id: {!r}".format(ex)))
    else:
        if value:
            message_id.defects.append(errors.InvalidHeaderDefect("Unexpected {!r}".format(value)))

    return message_id

class MessageIDHeaderCustom(MessageIDHeader):
    value_parser = staticmethod(parse_message_id)

def get_list(list_type, regex_list, regex_item, last_config=LAST_CONFIG):
    """
    Extract address lists from CS config filtered by regex matches on list name and item.

    :type list_type: str
    :type regex_list: str
    :type regex_item: str
    :type last_config: str
    :rtype: list
    """
    list_info = LIST_INFO[list_type]

    if list_info.tag_attribute is None:
        handler = HandlerValue(list_info.tag_table, list_info.tag_list, list_info.tag_item, regex_list, regex_item)
    else:
        handler = HandlerAttribute(list_info.tag_attribute, list_info.tag_table, list_info.tag_list, list_info.tag_item, regex_list, regex_item)

    parser = make_parser()
    parser.setContentHandler(handler)

    try:
        parser.parse(last_config)
    except SAXExceptionFinished:
        pass

    return handler.getLists()

def address_list(name_list):
    """
    Extract address list from CS config.

    :type name_list: str
    :rtype: list
    """
    extracted_list = get_list(LIST_ADDRESS, f"^{name_list}$", ".*")

    if extracted_list:
        return extracted_list[0][1]
    else:
        raise Exception(f"Address list '{name_list}' does not exist")

def lexical_list(name_list):
    """
    Extract lexical expression list from CS config.

    :type name_list: str
    :rtype: list
    """
    extracted_list = get_list(LIST_LEXICAL, f"^{name_list}$", ".*")

    if extracted_list:
        return extracted_list[0][1]
    else:
        raise Exception(f"Lexical list '{name_list}' does not exist")

def url_list(name_list):
    """
    Extract URL list from CS config.

    :type name_list: str
    :rtype: list
    """
    extracted_list = get_list(LIST_URL, f"^{name_list}$", ".*")

    if extracted_list:
        return extracted_list[0][1]
    else:
        raise Exception(f"URL list '{name_list}' does not exist")

def get_annotation(regex_annotation, last_config=LAST_CONFIG):
    """
    Extract annotations from CS config filtered by regex match on annotation name.

    :type regex_annotation: str
    :type last_config: str
    :rtype: list
    """
    handler = HandlerAnnotation(regex_annotation)

    parser = make_parser()
    parser.setContentHandler(handler)

    try:
        parser.parse(last_config)
    except SAXExceptionFinished:
        pass

    return handler.getAnnotations()

def annotation(name_annotation):
    """
    Extract annotation from CS config.

    :type name_annotation: str
    :rtype: TupleAnnotation
    """
    extracted_annotation = get_annotation(f"^{name_annotation}$")

    if extracted_annotation:
        return extracted_annotation[0]
    else:
        raise Exception(f"Annotation '{name_annotation}' does not exist")

def read_text(path_file, ignore_errors=False):
    """
    Read text file.

    :type path_file: str
    :type ignore_errors: bool
    :rtype: str
    """
    try:
        if ignore_errors:
            with open(path_file, errors="ignore") as f:
                content = f.read()
        else:
            with open(path_file) as f:
                content = f.read()
    except FileNotFoundError:
        raise Exception(f"'{path_file}' does not exist")
    except PermissionError:
        raise Exception(f"Cannot open '{path_file}'")
    except UnicodeDecodeError:
        raise Exception(f"'{path_file}' not UTF-8")

    return content

def read_binary(path_file):
    """
    Read binary file.

    :type path_file: str
    :rtype: bytes
    """
    try:
        with open(path_file, "rb") as f:
            content = f.read()
    except FileNotFoundError:
        raise Exception(f"'{path_file}' does not exist")
    except PermissionError:
        raise Exception(f"Cannot open '{path_file}'")

    return content

def python_charset(charset):
    """
    Convert charset name unsupported by Python to equivalent charset name supported by Python.

    :type charset: str
    :rtype: str
    """
    if charset is not None:
        lower = charset.lower()

        if lower in CHARSET_EQUIVALENT:
            return CHARSET_EQUIVALENT[lower]

    return charset

def get_text_content(part, errors="replace"):
    """
    Get text content from message part.

    :type part: EmailMessage
    :type errors: str
    :rtype: str
    """
    content = part.get_payload(decode=True)

    charset = python_charset(part.get_param("charset", "ascii"))

    return content.decode(charset, errors=errors)

def read_email(path_email, disable_splitting):
    """
    Parse email file.

    :type path_email: str
    :type disable_splitting: bool
    :rtype: email.message.Message
    """
    header_factory = HeaderRegistry(base_class=BaseHeaderCustom)
    header_factory.map_to_type("message-id", MessageIDHeaderCustom)

    email_policy = EmailPolicyCustom().clone(linesep="\r\n", header_factory=header_factory, disable_splitting=disable_splitting)
    email_policy.content_manager.add_get_handler("text", get_text_content)

    try:
        with open(path_email, "rb") as f:
            email = message_from_binary_file(f, policy=email_policy)
    except Exception:
        raise Exception("Cannot parse email")

    return email

def write_email(email, path_email, reformat_header):
    """
    Write email to file.

    :type email: email.message.Message
    :type path_email: str
    :type reformat_header: bool
    """
    if reformat_header:
        list_header = list()

        for (key, value) in email.items():
            list_header.append((key, sub(r"[ \n\r\t]+", " ", str(value))))

        for key in set(email.keys()):
            del email[key]

        for (key, value) in list_header:
            try:
                email[key] = value
            except ValueError:
                pass
            except Exception as ex:
                raise Exception(f"Cannot add '{key}' header: {ex}")

    try:
        email = email.as_bytes()
    except Exception:
        raise Exception("Cannot convert email to bytes")

    try:
        with open(path_email, "wb") as f:
            f.write(email)
    except Exception:
        raise Exception(f"Cannot write email to '{path_email}'")

def zip_encrypt(set_data, password):
    """
    Create encrypted zip archive from set of data with defined password and return as bytes.

    :type set_data: set
    :type password: str
    :rtype: bytes
    """
    buffer = BytesIO()

    with AESZipFile(buffer, "w", compression=ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
        zf.pwd = password

        for (file_name, data) in set_data:
            zf.writestr(file_name, data)

    return buffer.getvalue()

def unzip_decrypt(bytes_zip, password):
    """
    Extract encrypted zip archive with defined password and return as set of data.

    :type bytes_zip: bytes
    :type password: str
    :rtype: set
    """
    with AESZipFile(BytesIO(bytes_zip), "r", compression=ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
        zf.pwd = password

        set_data = set()

        for file_name in zf.namelist():
            set_data.add((file_name, zf.read(file_name)))

    return set_data

def end_escape(string):
    """
    Check string ending in uneven number of backslashes.

    :type string: str
    :rtype: bool
    """
    num_blackslash = 0

    for char in string[::-1]:
        if char == "\\":
            num_blackslash = num_blackslash + 1
        else:
            break

    return num_blackslash % 2 != 0

def extract_text(html):
    """
    Extract text from html.

    :type html: str
    :rtype: str
    """
    return "\n".join(etree.fromstring(html.encode(), parser=etree.HTMLParser()).xpath("//text()"))

def string_ascii(string):
    """
    Check whether string is ASCII.

    :type string: str
    :rtype: bool
    """
    try:
        string.encode("ascii")
    except UnicodeEncodeError:
        return False

    return True

def scan_sophos(path_file):
    """
    Scan file with Sophos AV and return name of virus found or None if clean.

    :type path_file: str
    :rtype: str or None
    """
    RUN_SOPHOS = [ "/opt/cs-gateway/bin/sophos/savfiletest", "-v", "-f" ]

    try:
        result = run(RUN_SOPHOS + [ path_file, ], check=True, stdout=PIPE, stderr=DEVNULL, encoding=CHARSET_UTF8)
    except Exception:
        raise Exception("Error calling Sophos AV")

    match = search(fr"\n\tSophosConnection::recvLine returning VIRUS (\S+) {path_file}\n", result.stdout)

    if match:
        return match.group(1)

    return None

def scan_kaspersky(path_file):
    """
    Scan file with Kaspersky AV and return name of virus found or None if clean.

    :type path_file: str
    :rtype: str or None
    """
    RUN_KASPERSKY = [ "/opt/cs-gateway/bin/kav/kavfiletest", "/tmp/.kavcom1", "/tmp/.kavscan1", "/tmp/.kavevent1" ]

    try:
        result = run(RUN_KASPERSKY + [ path_file, ], check=True, stdout=PIPE, stderr=DEVNULL, encoding=CHARSET_UTF8)
    except Exception:
        raise Exception("Error calling Kaspersky AV")

    match = search(fr"\n'{path_file}': EVENT_DETECT '([^']+)'. Detect type: ", result.stdout)

    if match:
        return match.group(1)

    return None

def avira_set(option_key, option_value, socket_avira):
    """
    Set Avira option.

    :type option_key: str
    :type option_value: str
    :type socket_avira: socket
    """
    bytes_key = option_key.encode()
    bytes_value = option_value.encode()

    socket_avira.send(b"SET " + bytes_key + b" " + bytes_value + b"\n")

    data = socket_avira.recv(BUFFER_TCP)

    if data != b"100 " + bytes_key + b":" + bytes_value + b"\n":
        raise Exception(f"Cannot set Avira option '{option_key}' to value '{option_value}'")

def scan_avira(path_file):
    """
    Scan file with Avira AV and return name of virus found or None if clean.

    :type path_file: str
    :rtype: str or None
    """
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect(( "127.0.0.1", 9999 ))

            data = s.recv(BUFFER_TCP)

            if data != b"100 SAVAPI:4.0\n":
                raise Exception

            avira_set("PRODUCT", "11906", s)
            avira_set("SCAN_TIMEOUT", "300", s)
            avira_set("ARCHIVE_SCAN", "1", s)

            s.send(b"SCAN " + path_file.encode() + b"\n")

            data = s.recv(BUFFER_TCP)
    except Exception:
        raise Exception("Error calling Avira AV")

    match = search(r"^310 [^;]*?(\S+) ;", data.decode())

    if match:
        return match.group(1)

    return None

def domain_blacklisted(domain):
    """
    Check domain against reputation blacklists.

    :type domain: str
    :rtype: str or None
    """
    for reputation in LIST_REPUTATION:
        try:
            set_result = { str(item) for item in resolve(f"{domain}.{reputation.query_domain}", reputation.record_type).rrset.items }
        except Exception:
            set_result = set()

        if len(set_result) == 1 and search(reputation.match, set_result.pop()):
            return reputation.query_domain

    return None

def url2regex(url):
    """
    Convert CS URL list entry to regex.

    :type url: str
    :rtype: str
    """
    match = search(PATTERN_PROTOCOL, url)

    if match is None:
        protocol = r"(https?://)?"
    else:
        protocol = match.group(1)

        url = match.group(2)

    split_url = url.split("/")

    if len(split_url) == 2 and split_url[1] == "*":
        return fr"^{protocol}{escape(split_url[0]).replace(r"\*", r".*")}/?.*$"
    else:
        return fr"^{protocol}{escape(url).replace(r"\*", r".*")}$"

def extract_part(email, content_type):
    """
    Extract part, charset and content for first non-attachment email part matching given content type.

    :type email: email.message.Message
    :type content_type: str
    :rtype: tuple or None
    """
    for part in email.walk():
        if part.get_content_type() == content_type and not part.is_attachment():
            charset = python_charset(part.get_content_charset())

            if charset is None:
                charset = CHARSET_UTF8

            try:
                content = part.get_payload(decode=True).decode(charset, errors="ignore").replace("\r", "")
            except Exception:
                raise Exception(f"Cannot decode '{content_type}' part with charset '{charset}'")

            return (part, charset, content)

    return None

def annotate_html(content, annotation, on_top=True):
    """
    Annotate HTML body.

    :type content: str
    :type annotation: str
    :type on_top: bool
    :rtype: str
    """
    if on_top:
        match = search(r"<body[^>]*>", content)

        if match is not None:
            index = match.end()
        else:
            match = search(r"<html[^>]*>", content)

            if match is not None:
                index = match.end()
            else:
                index = 0
    else:
        index = content.find("</body>")

        if index < 0:
            index = content.find("</html>")

            if index < 0:
                index = len(content) - 1

    return content[:index] + annotation + content[index:]

def url_blacklisted(url, set_whitelist, set_blacklist):
    """
    Check URL is blacklisted.

    :type url: str
    :type set_whitelist: set
    :type set_blacklist: set
    :rtype: tuple or None
    """
    if set_whitelist is not None:
        for pattern in set_whitelist:
            if search(pattern, url) is not None:
                return None

    if set_blacklist is not None:
        for pattern in set_blacklist:
            if search(pattern, url) is not None:
                return tuple()

    domain = search(PATTERN_DOMAIN, url).group(1).lower()

    while True:
        blacklist = domain_blacklisted(domain)

        if blacklist is not None:
            return ( domain, blacklist )

        index = domain.find(".")

        if index < 0:
            break

        domain = domain[index + 1:]

    return None
