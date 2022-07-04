# run_command.py V5.0.0
#
# Copyright (c) 2021-2022 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys
import re
import toml
from argparse import ArgumentParser
from xml.sax import make_parser, handler, SAXException

DESCRIPTION = "run external command"

LAST_CONFIG = "/var/cs-gateway/deployments/lastAppliedConfiguration.xml"

DEFAULT_LIBRARY = "External command library"

PATTERN_ARGUMENT = re.compile(r"^([^=]+)=(.*)")

@enum.unique
class ReturnCode(enum.IntEnum):
    """
    Return codes.

    100 - none
    101 - detected
    102 - modified
    199 - error
    255 - unhandled exception
    """
    NONE = 100
    DETECTED = 101
    MODIFIED = 102
    ERROR = 199
    EXCEPTION = 255

class SAXExceptionFinished(SAXException):
    """
    Custom SAXException for stopping parsing after all info has been read.
    """
    def __init__(self):
        super().__init__("Stop parsing")

class HandlerBase(handler.ContentHandler):
    """
    Base class of custom content handler for xml.sax for extracting lists from CS config filtered by regex matches on list name and item.
    """
    def __init__(self, tag_table, tag_list, tag_item, regex_list, regex_item):
        """
        :type tag_table: str
        :type tag_list: str
        :type tag_item: str
        :type regex_list: str
        :type regex_item: str
        """
        self.tag_table = tag_table
        self.tag_list = tag_list
        self.tag_item = tag_item
        self.pattern_list = re.compile(regex_list)
        self.pattern_item = re.compile(regex_item)
        self.list_itemlist = list()
        self.name_list = None
        self.list_item = None

        super().__init__()

    def getLists(self):
        """
        Return list of item lists.

        :rtype: list
        """
        return self.list_itemlist

class HandlerAttribute(HandlerBase):
    """
    Custom content handler for lists stored in tag attributes.
    """
    def __init__(self, tag_attribute, tag_table, tag_list, tag_item, regex_list, regex_item):
        """
        :type tag_attribute: str
        :type tag_table: str
        :type tag_list: str
        :type tag_item: str
        :type regex_list: str
        :type regex_item: str
        """
        self.tag_attribute = tag_attribute

        super().__init__(tag_table, tag_list, tag_item, regex_list, regex_item)

    def startElement(self, name, attrs):
        if name == self.tag_list and "name" in attrs:
            name_list = attrs["name"]

            if re.search(self.pattern_list, name_list):
                self.name_list = name_list
                self.list_item = list()
        elif self.name_list is not None and name == self.tag_item and self.tag_attribute in attrs:
            item = attrs[self.tag_attribute]

            if re.search(self.pattern_item, item):
                self.list_item.append(item)

    def endElement(self, name):
        if name == self.tag_list and self.name_list is not None:
            if self.list_item:
                self.list_itemlist.append(( self.name_list, self.list_item ))

            self.name_list = None
        elif name == self.tag_table:
            raise SAXExceptionFinished

def write_log(path_log, message):
    """
    Write message to log file.

    :type message: str
    :type path_log: str
    """
    LOG_PREFIX = ">>>>"
    LOG_SUFFIX = "<<<<"

    with open(path_log, "a") as file_log:
        file_log.write("{}{}{}\n".format(LOG_PREFIX, message, LOG_SUFFIX))

def extract_config(config, config_parameters):
    """
    Extract config parameters and check all required parameters are defined.

    :type config: list
    :type config_parameters: set
    :rtype: TupleConfig
    """
    try:
        config = toml.loads("\n".join(config))
    except Exception:
        raise Exception("Config not valid TOML format")

    # discard all parameters not defined in config_parameters
    config = { param_key: param_value for (param_key, param_value) in config.items() if param_key in config_parameters }

    # check for missing parameters
    parameters_missing = config_parameters - config.keys()

    if parameters_missing:
        raise Exception("Missing parameters {}".format(str(parameters_missing)[1:-1]))

    TupleConfig = namedtuple("TupleConfig", config_parameters)

    return TupleConfig(**config)

def extract_argument(argument):
    """
    Extract key and value from argument.

    :type argument: str
    :rtype: tuple
    """
    match = re.search(PATTERN_ARGUMENT, argument)

    if match is None:
        raise Exception("Invalid argument '{}'".format(argument))

    argument_key = match.group(1)

    if not argument_key:
        raise Exception("Argument key missing in '{}'".format(argument))

    argument_value = match.group(2)

    if not argument_value:
        raise Exception("Argument value missing in '{}'".format(argument))

    return ( argument_key, argument_value )

def extract_additional(additional, additional_arguments):
    """
    Extract additional arguments and check all required arguments are defined.

    :type additional: list
    :type additional_arguments: set
    :rtype: TupleAdditional
    """
    arguments_defined = dict()

    if additional is not None:
        for argument in additional:
            (argument_key, argument_value) = extract_argument(argument)

            if argument_key in additional_arguments:
                arguments_defined[argument_key] = argument_value

    # check for missing arguments
    arguments_missing = additional_arguments - arguments_defined.keys()

    if arguments_missing:
        raise Exception("Missing additional arguments {}".format(str(arguments_missing)[1:-1]))

    TupleAdditional = namedtuple("TupleAdditional", additional_arguments)

    return TupleAdditional(**arguments_defined)

def extract_optional(optional):
    """
    Extract optional arguments.

    :type optional: list
    :rtype: dict
    """
    dict_optional = dict()

    if optional is not None:
        for argument in optional:
            (argument_key, argument_value) = extract_argument(argument)

            dict_optional[argument_key] = argument_value

    return dict_optional

def main(args):
    if args.id is not None and args.id != "0":
        # skip embedded/attached SMTP messages
        return ReturnCode.NONE

    if args.config is None:
        pattern_list = r"^({}|{})$".format(re.escape(args.library), re.escape(args.command))
    else:
        pattern_list = r"^({}|{}|{})$".format(re.escape(args.library), re.escape(args.command), re.escape(args.config))

    handler_list = HandlerAttribute("text", "TextualAnalysisCollection", "TextualAnalysis", "Phrase", pattern_list, r".*")

    parser = make_parser()
    parser.setContentHandler(handler_list)

    try:
        parser.parse(LAST_CONFIG)
    except SAXExceptionFinished:
        pass
    except Exception:
        write_log(args.log, "Cannot extract lexical lists")

        return ReturnCode.ERROR

    library = None
    command = None
    config = None

    for (name, list_item) in handler_list.getLists():
        if name == args.library:
            library = list_item.pop()
        elif name == args.command:
            command = list_item.pop()
        elif args.config is not None and name == args.config:
            config = list_item

    if library is None:
        write_log(args.log, "Cannot extract library module")

        return ReturnCode.ERROR

    if command is None:
        write_log(args.log, "Cannot extract command module")

        return ReturnCode.ERROR

    if args.config is not None and config is None:
        write_log(args.log, "Cannot extract config list")

        return ReturnCode.ERROR

    try:
        exec(library, globals())
    except Exception:
        write_log(args.log, "Cannot load library module")

        return ReturnCode.ERROR

    try:
        exec(command, globals())
    except Exception:
        write_log(args.log, "Cannot load command module")

        return ReturnCode.ERROR

    if CONFIG_PARAMETERS:
        try:
            config = extract_config(config, CONFIG_PARAMETERS)
        except Exception as ex:
            write_log(args.log, ex)

            return ReturnCode.ERROR

    if ADDITIONAL_ARGUMENTS:
        try:
            additional = extract_additional(args.additional, ADDITIONAL_ARGUMENTS)
        except Exception as ex:
            write_log(args.log, ex)

            return ReturnCode.ERROR
    else:
        additional = None

    if OPTIONAL_ARGUMENTS:
        try:
            optional = extract_optional(args.optional)
        except Exception as ex:
            write_log(args.log, ex)

            return ReturnCode.ERROR
    else:
        optional = None

    return run_command(args.input, args.log, config, additional, optional, args.disable_splitting, args.reformat_header)

if __name__ == "__main__":
    parser = ArgumentParser(description=DESCRIPTION)
    parser.add_argument("input", metavar="INPUT", type=str, help="input file")
    parser.add_argument("log", metavar="LOG", type=str, help="log file")
    parser.add_argument("command", metavar="COMMAND", type=str, help="name of external command lexical list")
    parser.add_argument("-l", "--library", metavar="LIBRARY", type=str, default=DEFAULT_LIBRARY, help="name of external command library lexical list (default={})".format(DEFAULT_LIBRARY))
    parser.add_argument("-c", "--config", metavar="CONFIG", type=str, default=None, help="name of external command config lexical list (default=None)")
    parser.add_argument("-i", "--id", metavar="ID", type=str, default=None, help="item ID (default=None)")
    parser.add_argument("-a", "--additional", metavar="ADDITIONAL", action="append", type=str, help="additional arguments in 'key=value' format (default=None)")
    parser.add_argument("-o", "--optional", metavar="OPTIONAL", action="append", type=str, help="optional arguments in 'key=value' format (default=None)")
    parser.add_argument("-d", "--disable-splitting", action="store_true", help="disable MIME header parameter splitting according to RFC 2231")
    parser.add_argument("-r", "--reformat-header", action="store_true", help="reformat mail header")

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
