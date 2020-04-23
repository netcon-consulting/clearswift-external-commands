#!/bin/bash

# hybrid_scan.sh V1.1.0
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

API_HYBRID='https://www.hybrid-analysis.com/api/v2'
API_SUBMIT="$API_HYBRID/submit/file"
API_STATE="$API_HYBRID/report/IDENTIFIER/state"
API_VERDICT="$API_HYBRID/report/IDENTIFIER/summary"

HEADER_AGENT='user-agent: Falcon Sandbox'
HEADER_KEY="api-key: $API_KEY"

TYPE_WINDOWS=120
TYPE_LINUX=300

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
    echo "Usage: $(basename "$0") file_to_scan log_file"
    exit 99
fi

FILE_LOG="$2"

if ! [ -f "$1" ]; then
    write_log "Cannot open file '$1'"
    exit 99
fi

TYPE_INFO="$(objdump -f $1 | grep 'file format' | awk '{print $4}')"

case "$TYPE_INFO" in
    'elf32-i386' | 'elf64-x86-64' | 'elf32-x86-64')
        FILE_TYPE="$TYPE_LINUX";;
    'pei-i386' | 'pei-x86-64' | 'pe-i386')
        FILE_TYPE="$TYPE_WINDOWS";;
    *)
        write_log "Unknown file type '$TYPE_INFO'"
        exit 99;;
esac

SUBMIT_ANSWER="$(curl --silent -H "$HEADER_AGENT" -H "$HEADER_KEY" -F "file=@$1" -F "environment_id=$FILE_TYPE" -F 'no_share_third_party=true' -F 'allow_community_access=false' $API_SUBMIT)"

if [ -z "$SUBMIT_ANSWER" ]; then
    write_log 'Submit answer is empty'
    exit 99
fi

SUBMIT_HASH="$(echo $SUBMIT_ANSWER | awk 'match($0, /"sha256":"([^"]+)"/, a) {print a[1]}')"

if [ -z "$SUBMIT_HASH" ]; then
    write_log 'Cannot determine submit hash'
    exit 99
fi

API_STATE="$(echo $API_STATE | sed "s/IDENTIFIER/$SUBMIT_HASH:$FILE_TYPE/")"
API_VERDICT="$(echo $API_VERDICT | sed "s/IDENTIFIER/$SUBMIT_HASH:$FILE_TYPE/")"

while true; do
    sleep $TIME_WAIT
    STATE_ANSWER="$(curl --silent -H "$HEADER_AGENT" -H "$HEADER_KEY" $API_STATE)"

    if [ -z "$STATE_ANSWER" ]; then
        write_log 'State answer is empty'
        exit 99
    fi

    case "$(echo $STATE_ANSWER | awk 'match($0, /"state":"([^"]+)"/, a) {print a[1]}')" in
        'SUCCESS')
            VERDICT_ANSWER="$(curl --silent -H "$HEADER_AGENT" -H "$HEADER_KEY" $API_VERDICT)"

            if [ -z "$VERDICT_ANSWER" ]; then
                write_log 'Verdict answer is empty'
                exit 99
            fi

            VERDICT_RESULT="$(echo $VERDICT_ANSWER | awk 'match($0, /"verdict":"([^"]+)"/, a) {print a[1]}')"

            if [ -z "$VERDICT_RESULT" ]; then
                write_log 'Cannot determine verdict result'
                exit 99
            fi

            case "$VERDICT_RESULT" in
                'benign' | 'whitelisted')
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
            esac;;
        'ERROR')
            write_log 'Error during sandbox scan'
            exit 99;;
    esac
done
