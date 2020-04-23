#!/bin/bash

# add_external.sh V1.4.0
#
# Copyright (c) 2019 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - email not modified
# 1 - tag added to sender from email address
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

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $(basename "$0") email_file log_file"
    exit 99
fi

FILE_LOG="$2"

if ! [ -f "$1" ]; then
    write_log "Cannot open file '$1'"
    exit 99
fi

FROM_START="$(grep -n '^\(F\|f\)rom:' "$1" | head -1 | cut -f1 -d\:)"

FROM_END="$(expr $FROM_START + $(sed -n "$(expr $FROM_START + 1),\$ p" "$1" | grep -n '^\S' | head -1 | cut -f1 -d\:) - 1)"

FROM_LINE="$(sed -n "$FROM_START,$FROM_END{p}" "$1")"

if [ -z "$FROM_LINE" ]; then
    write_log 'From line is empty'
    exit 99
fi

FROM_KEYWORD="$(echo $FROM_LINE | cut -c -5)"
FROM_SENDER="$(echo $FROM_LINE | cut -c 6-)"

if [ -z "$FROM_SENDER" ]; then
    write_log 'From sender is empty'
    exit 99
fi

if ! echo "$FROM_SENDER" | grep -q '"\[EXT\] '; then
    FROM_ADDRESS="$(echo $FROM_SENDER | awk 'match($0, /<(.+@.+\..+)>/, a) {print a[1]}')"

    if [ -z "$FROM_ADDRESS" ]; then
        FROM_ADDRESS="$(echo $FROM_SENDER | awk 'match($0, /(.+@.+\..+)/, a) {print a[1]}')"

        if [ -z "$FROM_ADDRESS" ]; then
            write_log 'Empty email address'
            exit 99
        fi

        FROM_PREFIX="$(echo $FROM_SENDER | awk -F "$FROM_ADDRESS" '{print $1}' | sed 's/^\s*//g' | sed 's/\s*$//g' | sed -E 's/\"(.*)\"/\1/')"
        FROM_SUFFIX="$(echo $FROM_SENDER | awk -F "$FROM_ADDRESS" '{print $2}' | sed 's/^\s*//g' | sed 's/\s*$//g')"
    else
        FROM_PREFIX="$(echo $FROM_SENDER | awk -F "<$FROM_ADDRESS>" '{print $1}' | sed 's/^\s*//g' | sed 's/\s*$//g' | sed -E 's/\"(.*)\"/\1/')"
        FROM_SUFFIX="$(echo $FROM_SENDER | awk -F "<$FROM_ADDRESS>" '{print $2}' | sed 's/^\s*//g' | sed 's/\s*$//g')"
    fi

    FROM_NEW="$FROM_KEYWORD \"\[EXT\]"
    [ -z "$FROM_PREFIX" ] && FROM_NEW+=" $FROM_ADDRESS" || FROM_NEW+=" $FROM_PREFIX"
    FROM_NEW+="\" \<$FROM_ADDRESS\>"
    [ -z "$FROM_SUFFIX" ] || FROM_NEW+=" $FROM_SUFFIX"

    sed -i "$FROM_START,$FROM_END{d}" "$1"
    sed -i "${FROM_START}i $FROM_NEW" "$1"

    exit 1
fi

exit 0
