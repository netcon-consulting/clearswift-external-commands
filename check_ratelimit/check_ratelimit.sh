#!/bin/bash

# check_ratelimit.sh V1.1.0
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - rate limit not exceeded
# 1 - rate limit exceeded
# 99 - unrecoverable error

RATE_LIMIT=1000
TIME_EXPIRE=86400 # 24 hours
NAME_ADDRLIST='Rate limit whitelist'

DIR_ADDRESS='/var/cs-gateway/uicfg/policy/addresslists'

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

FROM_LINE="$(get_header "$1" 'from')"

if ! [ -z "$FROM_LINE" ]; then
    EMAIL_SENDER="$(echo $FROM_LINE | awk 'match($0, /[<"]?([^<"]+@[^">]+)[>"]?/, a) {print a[1]}')"

    if ! [ -z "$EMAIL_SENDER" ]; then
        redis-cli setex "$EMAIL_SENDER:$(date +%s.%N):$(uuidgen)" "$TIME_EXPIRE" 1 &>/dev/null

        if [ "$(redis-cli KEYS "$EMAIL_SENDER:*" | wc -l)" -gt "$RATE_LIMIT" ]; then
            FILE_ADDRESS="$(grep -l "AddressList name=\"$NAME_ADDRLIST\"" $DIR_ADDRESS/*.xml 2>/dev/null)"
            [ -z "$FILE_ADDRESS" ] || LIST_ADDRESS="$(xmlstarlet sel -t -m "AddressList/Address" -v . -n "$FILE_ADDRESS")"

            if [ -z "$LIST_ADDRESS" ]; then
                write_log "Empty address list"
                exit 99
            fi

            echo "$LIST_ADDRESS" | grep -q "^$EMAIL_SENDER$" || exit 1
        fi
    fi
fi

exit 0
