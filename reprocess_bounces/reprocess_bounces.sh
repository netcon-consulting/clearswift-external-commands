#!/bin/bash

# reprocess_bounces.sh V1.2.0
#
# Copyright (c) 2019-2020 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - skipped
# 1 - reprocessed
# 99 - unrecoverable error

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

# get header field by label
# parameters:
# $1 - email file
# $2 - header label
# return values:
# header field
get_header() {
    declare HEADER_START HEADER_END

    HEADER_START="$(grep -i -n "^$2:" "$1" | head -1 | cut -f1 -d\:)"

    [ -z "$HEADER_START" ] && return 1

    HEADER_END="$(sed -n "$(expr "$HEADER_START" + 1),\$ p" "$1" | grep -n '^\S' | head -1 | cut -f1 -d\:)"

    [ -z "$HEADER_END" ] && return 1

    HEADER_END="$(expr "$HEADER_START" + "$HEADER_END" - 1)"

    echo $(sed -n "$HEADER_START,$HEADER_END p" "$1") | awk 'match($0, /^[^ ]+: *(.*)/, a) {print a[1]}'
}

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $(basename "$0") email_file log_file"
    exit 99
fi

FILE_LOG="$2"

if ! [ -f "$1" ]; then
    write_log "Cannot open file '$1'"
    exit 99
fi

SUBJECT="$(get_header "$1" 'subject')"

if echo "$SUBJECT" | grep -q 'Undelivered Mail Returned to Sender'; then
    CONTENT_TYPE="$(get_header "$1" 'content-type')"

    if [ -z "$CONTENT_TYPE" ]; then
        write_log 'Content type is empty'
        exit 99
    fi

    BOUNDARY="$(echo "$CONTENT_TYPE" | awk 'match($0, /boundary="([^"]+)"/, a) {print a[1]}')"

    if [ -z "$BOUNDARY" ]; then
        write_log 'Boundary is empty'
        exit 99
    fi

    LIST_RECIPIENT="$(sed -n "/^Content-Description: Delivery report$/,/^--$(echo "$BOUNDARY" | sed 's/\//\\\//g')$/p" "$1" | awk 'match($0, /Final-Recipient: rfc822; (.+)/, a) {print a[1]}')"

    if [ -z "$LIST_RECIPIENT" ]; then
        write_log 'Recipient list is empty'
        exit 99
    fi

    MESSAGE="$(sed -n "/^Content-Description: Undelivered Message$/,/^--$(echo "$BOUNDARY" | sed 's/\//\\\//g')--$/p" "$1" | sed -n "/^Return-Path: <[^>]*>$/,/^--$(echo "$BOUNDARY" | sed 's/\//\\\//g')--$/p" | head -n -1)"

    if [ -z "$MESSAGE" ]; then
        write_log 'Message is empty'
        exit 99
    fi

    SENDER="$(echo "$MESSAGE" | grep '^Return-Path: <\S*>$' | awk 'match($0, /^Return-Path: <([^>]+)>$/, a) {print a[1]}')"

    for RECIPIENT in $LIST_RECIPIENT; do
       echo "$MESSAGE" | /usr/sbin/sendmail.postfix -f "$SENDER" "$RECIPIENT"
    done

    exit 1
fi

exit 0
