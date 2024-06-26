# check_internal.py V7.2.0
#
# Copyright (c) 2020-2024 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

from re import search
from email.utils import parseaddr
from ipaddress import IPv4Address, IPv4Network

ADDITIONAL_ARGUMENTS = ( )
OPTIONAL_ARGUMENTS = False
CONFIG_PARAMETERS = ( "internal_list", "internal_networks" )

def run_command(input, log, config, additional, optional, disable_splitting, reformat_header):
    """
    Check whether sender IP is in internal networks and sender domain is internal domain.

    :type input: str
    :type log: str
    :type config: TupleConfig
    :type additional: TupleAdditional
    :type optional: dict
    :type disable_splitting: bool
    :type reformat_header: bool
    """
    try:
        email = read_email(input, disable_splitting)
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    if "Received" not in email:
        write_log(log, "Received header does not exist")

        return ReturnCode.ERROR

    header_received = str(email.get("Received"))

    if not header_received:
        write_log(log, "Received header is empty")

        return ReturnCode.ERROR

    sender_ip = search(r"\[([0-9.]+)\]", header_received)

    if not sender_ip:
        write_log(log, "Cannot find sender IP")

        return ReturnCode.ERROR

    sender_ip = sender_ip.group(1)

    try:
        ipv4_address = IPv4Address(sender_ip)
    except Exception:
        write_log(log, "Invalid sender IP")

        return ReturnCode.ERROR

    for network in config.internal_networks:
        try:
            ipv4_network = IPv4Network(network)
        except Exception:
            write_log(log, f"Invalid CIDR '{network}'")

            return ReturnCode.ERROR

        if ipv4_address in ipv4_network:
            break
    else:
        return ReturnCode.NONE

    if "From" not in email:
        write_log(log, "From header does not exist")

        return ReturnCode.ERROR

    header_from = str(email["From"])

    if not header_from:
        write_log(log, "From header is empty")

        return ReturnCode.ERROR

    try:
        sender_address = parseaddr(header_from)[1]
    except Exception:
        write_log(log, "Cannot parse From header")

        return ReturnCode.ERROR

    if not sender_address:
        write_log(log, "Cannot find sender address")

        return ReturnCode.ERROR

    sender_address = sender_address.group(1)

    index_at = sender_address.find("@")

    if index_at == -1:
        write_log(log, "Invalid sender address")

        return ReturnCode.ERROR

    sender_domain = sender_address[index_at + 1:]

    if not sender_domain:
        write_log(log, "Empty sender domain")

        return ReturnCode.ERROR

    try:
        set_address = set(address_list(config.internal_list))
    except Exception as ex:
        write_log(log, ex)

        return ReturnCode.ERROR

    if not set_address:
        write_log(log, "Address list is empty")

        return ReturnCode.ERROR

    set_domain = { email_address[email_address.find("@") + 1:] for email_address in set_address }

    if sender_domain not in set_domain:
        return ReturnCode.NONE

    return ReturnCode.DETECTED
