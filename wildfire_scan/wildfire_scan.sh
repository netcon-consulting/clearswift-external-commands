#!/bin/bash

# wildfire_scan.sh V1.2.0
#
# Copyright (c) 2019 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - benign
# 1 - malware
# 2 - grayware
# 99 - unrecoverable error

##########################################
# please insert your own API key here:
##########################################
API_KEY='your_api_key_here'
##########################################

API_WILDFIRE='https://wildfire.paloaltonetworks.com/publicapi'
API_SUBMIT="$API_WILDFIRE/submit/file"
API_VERDICT="$API_WILDFIRE/get/verdict"

LOG_PREFIX='>>>>'
LOG_SUFFIX='<<<<'

TIME_WAIT=60 # in seconds

# writes message to log file with the defined log pre-/suffix 
# parameters:
# $1 - message
# return values:
# none
write_log() {
    echo "$LOG_PREFIX$1$LOG_SUFFIX" >> "$FILE_LOG"
}

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $(basename $0) file_to_scan log_file"
    exit 99
fi

FILE_LOG="$2"

if ! [ -f "$1" ]; then
    write_log "Cannot open file '$1'"
    exit 99
fi

SUBMIT_ANSWER="$(curl --silent -F "apikey=$API_KEY" -F "file=@$1" $API_SUBMIT)"

if [ -z "$SUBMIT_ANSWER" ]; then
    write_log 'Submit answer is empty'
    exit 99
fi

SUBMIT_HASH="$(echo $SUBMIT_ANSWER | awk 'match($0, /<sha256>([^<]+)<\/sha256>/, a) {print a[1]}')"

if [ -z "$SUBMIT_HASH" ]; then
    write_log 'Cannot determine submit hash'
    exit 99
fi

while true; do
    sleep $TIME_WAIT
    VERDICT_ANSWER="$(curl --silent -F "apikey=$API_KEY" -F "hash=$SUBMIT_HASH" $API_VERDICT)"

    if [ -z "$VERDICT_ANSWER" ]; then
        write_log 'Verdict answer is empty'
        exit 99
    fi

    VERDICT_RESULT="$(echo $VERDICT_ANSWER | awk 'match($0, /<verdict>([^<]+)<\/verdict>/, a) {print a[1]}')"

    if [ -z "$VERDICT_RESULT" ]; then
        write_log 'Cannot determine verdict result'
        exit 99
    fi

    case "$VERDICT_RESULT" in
        '-100')
            ;;
        '-101' | '-102' | '-103')
            write_log 'Verdict result error'
            exit 99;;
        '0')
            write_log "hash=$SUBMIT_HASH"
            exit 0;;
        '1')
            write_log "hash=$SUBMIT_HASH"
            exit 1;;
        '2')
            write_log "hash=$SUBMIT_HASH"
            exit 2;;
        *)
            write_log "Undefined verdict '$VERDICT_RESULT'"
            exit 99;;
    esac
done
