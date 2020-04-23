#!/bin/bash

# check_tls.sh V1.3.0
#
# Copyright (c) 2019 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Fabian Beckwilm (f.beckwilm@netcon-consulting.com)

# return codes:
# 0 - TLS supported
# 1 - TLS not supported
# 99 - unrecoverable error

EXPIRE_VALID=86400  # 24 hours
EXPIRE_INVALID=3600 # 1 hour
TIMEOUT=10
TLS_LOG="/var/log/cs-gateway/tls-$(date +%Y-%m-%d).log"

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
    echo "Usage: $(basename "$0") email_recipient log_file"
    exit 99
fi

DOMAIN_RECIPIENT="$(echo "$1" | awk -F"@" '{print $2}')"

if [ -z "$DOMAIN_RECIPIENT" ]; then
    write_log "Recipient domain is empty"
    exit 99
fi

LIST_SERVER="$(dig +short mx "$DOMAIN_RECIPIENT" | awk '{print $2}')"
TLS_VALID=0

for SERVER in $LIST_SERVER; do
    REDIS_RES="$(redis-cli GET tlstest:"$SERVER")"

    if [ "$REDIS_RES" == '(nil)' ] || [ "$REDIS_RES" == '' ]; then
        # Must check now
        TLSCHECK_CONNECT="$(echo 'quit' | timeout "$TIMEOUT" openssl s_client -showcerts -starttls smtp -connect "$SERVER":25 2>/dev/null)"

        if echo "$TLSCHECK_CONNECT" | grep -q 'Verify return code: 0 (ok)'; then
            echo "[$(date)] Valid: $DOMAIN_RECIPIENT: $SERVER" >> "$TLS_LOG"
            redis-cli SETEX tlstest:"$SERVER" "$EXPIRE_VALID" 1 > /dev/null # Silent
            TLS_VALID=1
        else
            echo "[$(date)] Invalid: $DOMAIN_RECIPIENT: $SERVER" >> "$TLS_LOG"
            redis-cli SETEX tlstest:"$SERVER" "$EXPIRE_INVALID" 0 > /dev/null # Silent
        fi
    else
        # Already got a response
        if [ "$REDIS_RES" = '1' ]; then
            echo "[$(date)] Valid (DB): $DOMAIN_RECIPIENT: $SERVER" >> "$TLS_LOG"
            TLS_VALID=1
        else
            echo "[$(date)] Invalid (DB): $DOMAIN_RECIPIENT: $SERVER" >> "$TLS_LOG"
        fi
    fi
done

[ "$TLS_VALID" = '1' ] && exit 0 || exit 1
