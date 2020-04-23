#!/bin/bash

# check_dkim.sh V1.6.0
#
# Copyright (c) 2019-2020 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - DKIM checked
# 99 - unrecoverable error

DKIM_LOG="/tmp/dkim-$(date +'%Y-%m').log"

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

HEADER_DKIM="$(get_header "$1" 'x-msw-original-dkim-signature')"

if ! [ -z "$HEADER_DKIM" ]; then
    HEADER_FROM="$(get_header "$1" 'from')"

    [ -z "$HEADER_FROM" ] && HEADER_FROM='<empty>'

    HEADER_TO="$(get_header "$1" 'to')"

    [ -z "$HEADER_TO" ] && HEADER_TO='<empty>'

    HEADER_SUBJECT="$(get_header "$1" 'subject')"

    [ -z "$HEADER_SUBJECT" ] && HEADER_SUBJECT='<empty>'

    echo "[$(date +'%F %T')] from=$HEADER_FROM, to=$HEADER_TO, subject=$HEADER_SUBJECT, dkim_domain=$(echo "$HEADER_DKIM" | awk 'match($0, /d=([^;]+);/, a) {print a[1]}'), dkim_selector=$(echo "$HEADER_DKIM" | awk 'match($0, /s=([^;]+);/, a) {print a[1]}')" >> "$DKIM_LOG"
fi
