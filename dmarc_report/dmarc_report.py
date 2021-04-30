#!/usr/bin/env python3

# dmarc_report.py V1.0.3
#
# Copyright (c) 2020-2021 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

import enum
import sys

#########################################################################################

from string import Template
from xml.etree import ElementTree
import syslog
from netcon import ParserArgs, read_file, write_log

DESCRIPTION = "parse DMARC xml reports and write results to syslog"

@enum.unique
class ReturnCode(enum.IntEnum):
    """
    Return codes.

    0   - DMARC report successfully parsed
    99  - error
    255 - unhandled exception
    """
    SUCCESS = 0
    ERROR = 99
    EXCEPTION = 255

CONFIG_PARAMETERS = ( )

TEMPLATE_SYSLOG = Template("org=$name_org, id=$id_report, begin=$date_begin, end=$date_end, domain=$domain, ip=$ip_source, count=$count, disposition=$disposition, dkim=$dkim, spf=$spf")

def main(args):
    try:
        xml_report = read_file(args.input, ignore_errors=True)
    except Exception as ex:
        write_log(args.log, ex)

        return ReturnCode.ERROR

    try:
        syslog.openlog("dmarc_report", facility=syslog.LOG_MAIL)
    except Exception:
        write_log(args.log, "Cannot connect to syslog")

        return ReturnCode.ERROR

    try:
        tree = ElementTree.fromstring(xml_report)
    except Exception:
        write_log(args.log, "Cannot parse xml")

        return ReturnCode.ERROR

    name_org = None
    id_report = None
    date_begin = None
    date_end = None
    domain = None

    for child in tree:
        if child.tag == "report_metadata":
            for grandchild in child:
                if grandchild.tag == "org_name":
                    name_org = grandchild.text
                elif grandchild.tag == "report_id":
                    id_report = grandchild.text
                elif grandchild.tag == "date_range":
                    for grandgrandchild in grandchild:
                        if grandgrandchild.tag == "begin":
                            date_begin = grandgrandchild.text
                        elif grandgrandchild.tag == "end":
                            date_end = grandgrandchild.text
        elif child.tag == "policy_published":
            for grandchild in child:
                if grandchild.tag == "domain":
                    domain = grandchild.text
        elif child.tag == "record":
            for grandchild in child:
                if grandchild.tag == "row":
                    ip_source = None
                    count = None
                    disposition = None
                    dkim = None
                    spf = None

                    for grandgrandchild in grandchild:
                        if grandgrandchild.tag == "source_ip":
                            ip_source = grandgrandchild.text
                        elif grandgrandchild.tag == "count":
                            count = grandgrandchild.text
                        elif grandgrandchild.tag == "policy_evaluated":
                            for grandgrandgrandchild in grandgrandchild:
                                if grandgrandgrandchild.tag == "disposition":
                                    disposition = grandgrandgrandchild.text
                                elif grandgrandgrandchild.tag == "dkim":
                                    dkim = grandgrandgrandchild.text
                                elif grandgrandgrandchild.tag == "spf":
                                    spf = grandgrandgrandchild.text

                    syslog.syslog(TEMPLATE_SYSLOG.substitute(name_org=name_org, id_report=id_report, date_begin=date_begin, date_end=date_end, domain=domain, ip_source=ip_source, count=count, disposition=disposition, dkim=dkim, spf=spf))

                    break

    return ReturnCode.SUCCESS

#########################################################################################

if __name__ == "__main__":
    parser = ParserArgs(DESCRIPTION, config=bool(CONFIG_PARAMETERS))

    args = parser.parse_args()

    try:
        sys.exit(main(args))
    except Exception:
        # should never get here; exceptions must be handled in main()
        sys.exit(ReturnCode.EXCEPTION)
