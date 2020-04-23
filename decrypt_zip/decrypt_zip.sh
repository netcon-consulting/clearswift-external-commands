#!/bin/bash

# decrypt_zip.sh V1.2.0
#
# Copyright (c) 2019 NetCon Unternehmensberatung GmbH, netcon-consulting.com
#
# Author: Marc Dierksen (m.dierksen@netcon-consulting.com)

# return codes:
# 0 - zip file successfully decrypted
# 1 - zip file successfully decrypted but virus found
# 2 - zip file cannot be decrypted with any of the provided passwords
# 99 - unrecoverable error

FILE_PASSWORD='/opt/cs-gateway/scripts/netcon/zip_passwords.txt'

DIR_EXTRACT='/tmp/TMPextract'

FILE_DEBUG='/var/log/decrypt_zip.log'

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

# writes message to debug log file
# parameters:
# $1 - message
# return values:
# none
write_debug() {
    echo "[$(date +'%F %T')] $1" >> "$FILE_DEBUG"
}

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $(basename "$0") encrypted_zip log_file"
    exit 99
fi

FILE_LOG="$2"

if ! [ -f "$1" ]; then
    write_log "Cannot open file '$1'"
    exit 99
fi

if ! [ -f "$FILE_PASSWORD" ]; then
    write_log "Cannot open password list '$FILE_PASSWORD'"
    exit 99
fi

write_debug "Decrypting '$1'..."

rm -rf "$DIR_EXTRACT"
mkdir -p "$DIR_EXTRACT"

COUNTER=1
while read -r PASSWORD; do
    RESULT_EXTRACT="$(unzip -P "$PASSWORD" -d "$DIR_EXTRACT" "$1" 2>&1)"
    if [ "$?" = 0 ] && ! echo "$RESULT_EXTRACT" | grep -q 'incorrect password'; then
        VIRUS_FOUND=''
        for FILE in $(find "$DIR_EXTRACT" -type f -exec echo {} \;); do
            write_debug "Scanning '$FILE'"
            if /opt/cs-gateway/bin/sophos/savtest -v -f "$FILE" 2>/dev/null | grep -q VIRUS; then
                VIRUS_FOUND=1
                write_debug "Virus found in '$FILE'"
                break
            fi
        done
        write_log "password $COUNTER"
        rm -rf "$DIR_EXTRACT"
        if [ "$VIRUS_FOUND" = 1 ]; then
            write_debug "File '$1' successfully decrypted with password $COUNTER but virus found"
            exit 1
        else
            write_debug "File '$1' successfully decrypted with password $COUNTER"
            exit 0
        fi
    fi
    COUNTER="$(expr $COUNTER + 1)"
done < "$FILE_PASSWORD"

write_debug "File '$1' cannot be decrypted"
rm -rf "$DIR_EXTRACT"
exit 2
