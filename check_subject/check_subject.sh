#!/bin/bash

# check_subject.sh V1.0.0
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - email containes search string
# 1 - email does not contain search string
# 99 - unrecoverable error

SEARCH_STRING='privat'

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

SUBJECT_HEADER="$(get_header "$1" 'subject')"

if [ -z "$SUBJECT_HEADER" ]; then
    write_log 'Cannot find subject header'
    exit 99
fi

echo "$SUBJECT_HEADER" | grep -E -q -i "(^| )$SEARCH_STRING($| )" || exit 1
