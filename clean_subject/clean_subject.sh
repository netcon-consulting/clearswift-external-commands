#!/bin/bash

# clean_subject.sh V1.2.0
#
# Copyright (c) 2019-2020 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - email not modified
# 1 - one or more keywords removed from subject
# 99 - unrecoverable error

LOG_PREFIX='>>>>'
LOG_SUFFIX='<<<<'

LAST_CONFIG='/var/cs-gateway/deployments/lastAppliedConfiguration.xml'
DIR_LEXICAL='/var/cs-gateway/uicfg/policy/ta'
NAME_LEXICAL='Clean subject'

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

# replace header field by label
# parameters:
# $1 - email file
# $2 - header label
# $3 - new header
# return values:
# none
replace_header() {
    declare HEADER_START HEADER_END

    HEADER_START="$(grep -i -n "^$2:" "$1" | head -1 | cut -f1 -d\:)"

    if [ -z "$HEADER_START" ]; then
        write_log "Cannot find start of '$2' header line"
        exit 99
    fi

    HEADER_END="$(sed -n "$(expr $HEADER_START + 1),\$ p" "$1" | grep -n '^\S' | head -1 | cut -f1 -d\:)"

    if [ -z "$HEADER_END" ]; then
        write_log 'Cannot find end of '$2' header line'
        exit 99
    fi

    HEADER_END="$(expr "$HEADER_START" + "$HEADER_END" - 1)"

    sed -i "$HEADER_START,$HEADER_END d" "$1"
    sed -i "$HEADER_START i $2: $3" "$1"
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

HEADER_SUBJECT="$(get_header "$1" 'subject')"

if ! [ -z "$HEADER_SUBJECT" ]; then
    FILE_LEXICAL="$(grep -l "name=\"$NAME_LEXICAL\"" $DIR_LEXICAL/*.xml 2>/dev/null)"
    [ -z "$FILE_LEXICAL" ] || LIST_LEXICAL="$(xmlstarlet sel -t -m "TextualAnalysis/Phrase" -v @text -n "$FILE_LEXICAL")"

    if ! [ -z "$LIST_LEXICAL" ]; then
        MODIFIED=0

        for KEYWORD in $LIST_LEXICAL; do
            if echo "$HEADER_SUBJECT" | grep -q "$KEYWORD"; then
                HEADER_SUBJECT="$(echo "$HEADER_SUBJECT" | sed "s/$KEYWORD *//g")"

                MODIFIED=1
            fi
        done

        if [ "$MODIFIED" = 1 ]; then
            replace_header "$1" 'subject' "$HEADER_SUBJECT"
            exit 1
        fi
    fi
fi

exit 0
