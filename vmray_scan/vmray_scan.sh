#!/bin/bash

# vmray_scan.sh V1.1.0
#
# Copyright (c) 2019 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - benign
# 1 - malware
# 2 - grayware
# 99 - unrecoverable error

##########################################################################
# please insert your own API key here:
##########################################################################
API_KEY='your_api_key_here'
##########################################################################

API_VMRAY='https://cloud.vmray.com'
API_SUBMIT="$API_VMRAY/rest/sample/submit"
API_STATE="$API_VMRAY/rest/submission/IDENTIFIER"
API_VERDICT="$API_VMRAY/rest/sample/sha256/IDENTIFIER"

HEADER_KEY="Authorization: api_key $API_KEY"

LOG_PREFIX='>>>>'
LOG_SUFFIX='<<<<'

TIME_WAIT=120 # in seconds

# writes message to log file with the defined log pre-/suffix 
# parameters:
# $1 - message
# return values:
# none
write_log() {
    echo "$LOG_PREFIX$1$LOG_SUFFIX" >> "$FILE_LOG"
}

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $(basename "$0") file_to_scan log_file"
    exit 99
fi

FILE_LOG="$2"

if ! [ -f "$1" ]; then
    write_log "Cannot open file '$1'"
    exit 99
fi

SUBMIT_ANSWER="$(curl --silent -H "$HEADER_KEY" -F "sample_file=@$1" $API_SUBMIT)"

if [ -z "$SUBMIT_ANSWER" ]; then
    write_log 'Submit answer is empty'
    exit 99
fi

SUBMIT_HASH="$(echo $SUBMIT_ANSWER | awk 'match($0, /"submission_sample_sha256": "([^"]+)"/, a) {print a[1]}')"

if [ -z "$SUBMIT_HASH" ]; then
    write_log 'Cannot determine submit hash'
    exit 99
fi

SUBMIT_ID="$(echo $SUBMIT_ANSWER | awk 'match($0, /"submission_id": ([^,]+),/, a) {print a[1]}')"

if [ -z "$SUBMIT_ID" ]; then
    write_log 'Cannot determine submit ID'
    exit 99
fi

API_STATE="$(echo $API_STATE | sed "s/IDENTIFIER/$SUBMIT_ID/")"
API_VERDICT="$(echo $API_VERDICT | sed "s/IDENTIFIER/$SUBMIT_HASH/")"

while true; do
    sleep $TIME_WAIT
    STATE_ANSWER="$(curl --silent -H "$HEADER_KEY" $API_STATE)"

    if [ -z "$STATE_ANSWER" ]; then
        write_log 'State answer is empty'
        exit 99
    fi

    if [ "$(echo $STATE_ANSWER | awk 'match($0, /"submission_has_errors": ([^,]+),/, a) {print a[1]}')" = 'true' ]; then
        write_log 'Error during sandbox scan'
        exit 99
    fi

    if [ "$(echo $STATE_ANSWER | awk 'match($0, /"submission_finished": ([^,]+),/, a) {print a[1]}')" = 'true' ]; then
        VERDICT_ANSWER="$(curl --silent -H "$HEADER_KEY" $API_VERDICT)"

        if [ -z "$VERDICT_ANSWER" ]; then
            write_log 'Verdict answer is empty'
            exit 99
        fi

        VERDICT_RESULT="$(echo $VERDICT_ANSWER | awk 'match($0, /"sample_highest_vti_severity": "([^"]+)"/, a) {print a[1]}')"

        if [ -z "$VERDICT_RESULT" ]; then
            write_log 'Cannot determine verdict result'
            exit 99
        fi

        case "$VERDICT_RESULT" in
            'not_suspicious')
                write_log "hash=$SUBMIT_HASH"
                exit 0;;
            'malicious')
                write_log "hash=$SUBMIT_HASH"
                exit 1;;
            'suspicious')
                write_log "hash=$SUBMIT_HASH"
                exit 2;;
            *)
                write_log "Undefined verdict '$VERDICT_RESULT'"
                exit 99;;
        esac
    fi
done
