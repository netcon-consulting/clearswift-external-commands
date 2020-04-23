#!/bin/bash

# check_iprange.sh V1.0.0
#
# Copyright (c) 2019 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - sender IP not in defined ranges
# 1 - sender IP in defined ranges
# 99 - unrecoverable error

LIST_RANGE=()
LIST_RANGE+=('40.92.0.1,40.93.255.254')
LIST_RANGE+=('40.107.0.1,40.107.255.254')
LIST_RANGE+=('52.100.0.1,52.103.255.254')
LIST_RANGE+=('104.47.0.1,104.47.127.254')

LOG_PREFIX='>>>>'
LOG_SUFFIX='<<<<'

# writes message to log file with the defined log pre-/suffix 
# parameters:
# $1 - message
# return values:
# none
write_log() {
    echo "$LOG_PREFIX$1$LOG_SUFFIX" >> "$FILE_LOG"
}

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $(basename "$0") email log_file"
    exit 99
fi

FILE_LOG="$2"

if ! [ -f "$1" ]; then
    write_log "Cannot open file '$1'"
    exit 99
fi

RECEIVED_START="$(grep -n '^Received: from' "$1" | head -1 | cut -f1 -d\:)"

if [ -z "$RECEIVED_START" ]; then
    write_log 'Cannot find start of received from line'
    exit 99
fi

RECEIVED_END="$(expr $RECEIVED_START + $(sed -n "$(expr $RECEIVED_START + 1),\$ p" "$1" | grep -n '^\S' | head -1 | cut -f1 -d\:) - 1)"

if [ -z "$RECEIVED_END" ]; then
    write_log 'Cannot find end of received from line'
    exit 99
fi

RECEIVED_LINE="$(sed -n "$RECEIVED_START,$RECEIVED_END{p}" "$1")"

if [ -z "$RECEIVED_LINE" ]; then
    write_log 'Received from line is empty'
    exit 99
fi

IP_ADDRESS="$(echo $RECEIVED_LINE | awk 'match($0, /\[([0-9.]+)\]/, a) {print a[1]}')"

if [ -z "$IP_ADDRESS" ]; then
    write_log 'Cannot find IP address'
    exit 99
fi

OCTET1="$(echo $IP_ADDRESS | awk -F. '{print $1}')"
OCTET2="$(echo $IP_ADDRESS | awk -F. '{print $2}')"
OCTET3="$(echo $IP_ADDRESS | awk -F. '{print $3}')"
OCTET4="$(echo $IP_ADDRESS | awk -F. '{print $4}')"

for IP_RANGE in ${LIST_RANGE[@]}; do
    IP_MIN=$(echo $IP_RANGE | awk -F, '{print $1}')
    OCTET1_MIN="$(echo $IP_MIN | awk -F. '{print $1}')"
    OCTET2_MIN="$(echo $IP_MIN | awk -F. '{print $2}')"
    OCTET3_MIN="$(echo $IP_MIN | awk -F. '{print $3}')"
    OCTET4_MIN="$(echo $IP_MIN | awk -F. '{print $4}')"

    IP_MAX=$(echo $IP_RANGE | awk -F, '{print $2}')
    OCTET1_MAX="$(echo $IP_MAX | awk -F. '{print $1}')"
    OCTET2_MAX="$(echo $IP_MAX | awk -F. '{print $2}')"
    OCTET3_MAX="$(echo $IP_MAX | awk -F. '{print $3}')"
    OCTET4_MAX="$(echo $IP_MAX | awk -F. '{print $4}')"

    if [ "$OCTET1" -ge "$OCTET1_MIN" ] && [ "$OCTET1" -le "$OCTET1_MAX" ]           \
        && [ "$OCTET2" -ge "$OCTET2_MIN" ] && [ "$OCTET2" -le "$OCTET2_MAX" ]       \
        && [ "$OCTET3" -ge "$OCTET3_MIN" ] && [ "$OCTET3" -le "$OCTET3_MAX" ]       \
        && [ "$OCTET4" -ge "$OCTET4_MIN" ] && [ "$OCTET4" -le "$OCTET4_MAX" ]; then
        exit 1
    fi
done
