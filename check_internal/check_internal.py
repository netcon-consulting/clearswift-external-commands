#!/usr/bin/env python3

# check_internal.py V1.2.0
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

import re
from ipaddress import IPv4Address, IPv4Network
from netcon import ParserArgs, read_config, read_email, write_log, get_address_list, extract_email_address

DESCRIPTION = "checks sender IP in defined internal networks and sender domain on defined address list"

class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0  - sender IP not in defined internal networks or sender domain not on defined address list
    1  - sender IP in defined internal networks and sender domain on defined address list
    99 - error
    255 - unhandled exception
    """
    SENDER_EXTERNAL = 0
    SENDER_INTERNAL = 1
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( "name_address_list", "internal_networks" )

def main(args):
    try:
        config = read_config(args.config, CONFIG_PARAMETERS)

        email = read_email(args.input)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    header_received = email.get("Received")

    if not header_received:
        write_log(args.log, "Header received is empty")

        return ReturnCode.ERROR

    sender_ip = re.search(r"\[([0-9.]+)\]", header_received)

    if not sender_ip:
        write_log(args.log, "Cannot find sender IP")

        return ReturnCode.ERROR

    sender_ip = sender_ip.group(1)

    try:
        ipv4_address = IPv4Address(sender_ip)
    except:
        write_log(args.log, "Invalid sender IP")

        return ReturnCode.ERROR

    for network in config.internal_networks:
        try:
            ipv4_network = IPv4Network(network)
        except:
            write_log(args.log, "Invalid CIDR '{}'".format(network))

            return ReturnCode.ERROR

        if ipv4_address in ipv4_network:
            break
    else:
        return ReturnCode.SENDER_EXTERNAL

    header_from = email.get("From")

    if not header_from:
        write_log(args.log, "Header from is empty")

        return ReturnCode.ERROR

    sender_address = extract_email_address(header_from)

    if not sender_address:
        write_log(args.log, "Cannot find sender address")

        return ReturnCode.ERROR

    sender_address = sender_address.group(1)

    index_at = sender_address.find("@")

    if index_at == -1:
        write_log(args.log, "Invalid sender address")

        return ReturnCode.ERROR

    sender_domain = sender_address[index_at + 1:]

    if not sender_domain:
        write_log(args.log, "Empty sender domain")

        return ReturnCode.ERROR

    try:
        set_address = get_address_list(config.name_address_list)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    if not set_address:
        write_log(args.log, "Address list is empty")

        return ReturnCode.ERROR

    set_domain = { email_address[email_address.find("@") + 1:] for email_address in set_address }

    if sender_domain not in set_domain:
        return ReturnCode.SENDER_EXTERNAL

    return ReturnCode.SENDER_INTERNAL

#########################################################################################

if __name__ == "__main__":
    if CONFIG_PARAMETERS:
        if __file__.endswith(".py"):
            config_default = __file__[:-3] + ".toml"
        else:
            config_default = __file__ + ".toml"

        parser = ParserArgs(DESCRIPTION, config_default=config_default)
    else:
        parser = ParserArgs(DESCRIPTION)

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
