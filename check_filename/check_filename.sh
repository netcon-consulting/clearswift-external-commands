#!/bin/bash

# check_filename.sh V1.2.0
#
# Copyright (c) 2020 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - no blacklisted filename found
# 1 - blacklisted filename found
# 99 - unrecoverable error

LOG_PREFIX='>>>>'
LOG_SUFFIX='<<<<'

DIR_LEXICAL='/var/cs-gateway/uicfg/policy/ta'
NAME_LEXICAL='Filename blacklist'

# writes message to log file with the defined log pre-/suffix 
# parameters:
# $1 - message
# return values:
# none
write_log() {
    echo "$LOG_PREFIX$1$LOG_SUFFIX" >> "$FILE_LOG"
}

# get header fields by label
# parameters:
# $1 - email file
# $2 - header label
# return values:
# list of header fields
get_header() {
    declare LIST_START HEADER_START HEADER_END

    LIST_START="$(grep -i -n "^$2:" "$1" | cut -f1 -d\:)"

    [ -z "$LIST_START" ] && return 1

    for HEADER_START in $LIST_START; do
        HEADER_END="$(sed -n "$(expr "$HEADER_START" + 1),\$ p" "$1" | grep -E -n '^(\S|$)' | head -1 | cut -f1 -d\:)"

        if ! [ -z "$HEADER_END" ]; then
            HEADER_END="$(expr "$HEADER_START" + "$HEADER_END" - 1)"

            sed -n "$HEADER_START,$HEADER_END p" "$1" | tr '\n' ' ' | sed 's/ $//' | awk 'match($0, /^[^ ]+: *(.*)/, a) {print a[1]}'
        fi
    done
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

FILE_LEXICAL="$(grep -l "name=\"$NAME_LEXICAL\"" $DIR_LEXICAL/*.xml 2>/dev/null)"

if [ -z "$FILE_LEXICAL" ]; then
    write_log "Cannot find lexical list '$NAME_LEXICAL'"

    exit 99
fi

LIST_LEXICAL="$(xmlstarlet sel -t -m "TextualAnalysis/Phrase" -v @text -n "$FILE_LEXICAL" | sed '/^$/d')"

if ! [ -z "$LIST_LEXICAL" ]; then
    LIST_FILE="$(get_header "$1" 'content-\(disposition\|type\)' | awk 'match($0, /(file)?name="?([^"]+)"?/, a) {print a[2]}')"

    if ! [ -z "$LIST_FILE" ]; then
        while read REGEXP; do
            if echo "$LIST_FILE" | grep -P -q "^$REGEXP$"; then
                write_log "$REGEXP"

                exit 1
            fi
        done < <(echo "$LIST_LEXICAL")
    fi
fi

exit 0
