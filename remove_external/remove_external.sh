#!/bin/bash

# remove_external.sh V1.4.0
#
# Copyright (c) 2019 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - email not modified
# 1 - tag removed from recipient to and/or CC email addresses
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

MODIFIED=''

if grep -q '^\(T\|t\)o: "\[EXT\] ' "$1"; then
    sed -i 's/^\(T\|t\)o: "\[EXT\] /\1o: "/' "$1"
    MODIFIED=1
fi

if grep -q '^\(\(C\|c\)\{2\}\): "\[EXT\] ' "$1"; then
    sed -i 's/^\(\(C\|c\)\{2\}\): "\[EXT\] /\1: "/' "$1"
    MODIFIED=1
fi

[ "$MODIFIED" = 1 ] && exit 1 || exit 0
