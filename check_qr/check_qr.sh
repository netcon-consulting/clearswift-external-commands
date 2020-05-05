#!/bin/bash

# check_qr.sh V1.20.0
#
# Copyright (c) 2019-2020 NetCon Unternehmensberatung GmbH, https://www.netcon-consulting.com
#
# Authors:
# Marc Dierksen (m.dierksen@netcon-consulting.com)
# Spyros Delimpasis (sdelimpasis@inter-datasecurity.com)

# return codes:
# 0 - picture does contain no QR code with URL or URL domain is on custom whitelist or not listed on online blacklist
# 1 - picture contains QR code with URL and URL domain is on custom or online blacklist
# 99 - unrecoverable error

LOG_PREFIX='>>>>'
LOG_SUFFIX='<<<<'

DIR_URL='/var/cs-gateway/uicfg/policy/urllists'
NAME_WHITELIST='Whitelist Domain'
NAME_BLACKLIST='Blacklist Domain'
LIST_MULTI='surbl.org uribl.com'

# writes message to log file with the defined log pre-/suffix 
# parameters:
# $1 - message
# return values:
# none
write_log() {
    echo "$LOG_PREFIX$1$LOG_SUFFIX" >> "$FILE_LOG"
}

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $(basename "$0") image_file log_file"
    exit 99
fi

FILE_LOG="$2"

if ! [ -f "$1" ]; then
    write_log "Cannot open file '$1'"
    exit 99
fi

if ! which zbarimg &>/dev/null; then
    write_log "'zbarimg' needs to be installed"
    exit 99
fi

RESULT="$(zbarimg "$1" 2>/dev/null)"

if [ "$?" = 0 ] && echo "$RESULT" | grep -q '^QR-Code:'; then
	# Check if content matches bitcoin wallet ID pattern
	if  echo "$RESULT" | egrep -q --regexp='[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'; then
		write_log "Bitcoin address detected"
		exit 1
	fi

    LIST_URL="$(echo $RESULT | awk '{pattern="((https?://|www.|ftp.)[^ ]+)"; while (match($0, pattern, arr)) {val = arr[1]; print val; sub(pattern, "")}}')"

    if ! [ -z "$LIST_URL" ]; then
        NAME_DOMAIN="$(echo "$URL" | awk 'match($0, /(https?:\/\/)?([^ \/]+)/, a) {print a[2]}')"

        FILE_WHITE="$(grep -l "UrlList name=\"$NAME_WHITELIST\"" $DIR_URL/*.xml 2>/dev/null)"
        [ -z "$FILE_WHITE" ] || LIST_WHITE="$(xmlstarlet sel -t -m "UrlList/Url" -v . -n "$FILE_WHITE")"

        FILE_BLACK="$(grep -l "UrlList name=\"$NAME_BLACKLIST\"" $DIR_URL/*.xml 2>/dev/null)"
        [ -z "$FILE_BLACK" ] || LIST_BLACK="$(xmlstarlet sel -t -m "UrlList/Url" -v . -n "$FILE_BLACK")"

        for URL in $LIST_URL; do
			# Check if URL contains IP address
			if  echo "$URL" | egrep -q --regexp='(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])'; then
				write_log "Link with IP address instead of domain name"
				exit 1
			fi

			# Check if URL redirects to another URL. Target URL is used for lookups
			REDIRECTION="$(curl -sLI "$URL" | grep -i 'location' | sed 's/^.*: //')"

			if ! [ -z "$REDIRECTION" ] && [ "$?" = 0 ] ; then
				NAME_DOMAIN="$(echo "$REDIRECTION" | tr '[:upper:]' '[:lower:]' | awk 'match($0, /(https?:\/\/)?([^ \/]+)/, a) {print a[2]}')"
			else
				NAME_DOMAIN="$(echo "$URL" | tr '[:upper:]' '[:lower:]'| awk 'match($0, /(https?:\/\/)?([^ \/]+)/, a) {print a[2]}')"
			fi

            DOMAIN_PARTIAL="$NAME_DOMAIN"
            DOMAIN_WHITELISTED=0

            while true; do
                if ! [ -z "$LIST_BLACK" ] && echo "$LIST_BLACK" | grep -q "^$DOMAIN_PARTIAL$"; then
                    write_log "$URL [$NAME_BLACKLIST]"
                    exit 1
                elif ! [ -z "$LIST_WHITE" ] && echo "$LIST_WHITE" | grep -q "^$DOMAIN_PARTIAL$"; then
                    DOMAIN_WHITELISTED=1
                    break
                fi

                echo "$DOMAIN_PARTIAL" | grep -q '\.' || break

                DOMAIN_PARTIAL="$(echo "$DOMAIN_PARTIAL" | sed -E 's/[^.]+.//')"
            done

            if [ "$DOMAIN_WHITELISTED" != 1 ]; then
                RESULT="$(dig +short "$NAME_DOMAIN.dnsbl7.mailshell.net" 2>/dev/null)"

                if [ "$?" = 0 ]; then
                    RESULT="$(echo "$RESULT" | awk -F. '{print $4}')"

                    if ! [ -z "$RESULT" ] && [ "$RESULT" != '100' ] && [ "$RESULT" != '101' ]; then
                        write_log "$URL [mailshell.net]"
                        exit 1
                    fi
                fi

                for BLACKLIST in $LIST_MULTI; do
                    RESULT="$(dig txt +short "$NAME_DOMAIN.multi.$BLACKLIST" 2>/dev/null)"

                    if [ "$?" = 0 ] && ! [ -z "$RESULT" ] && ! echo "$RESULT" | grep -q 'Query Refused'; then
                        write_log "$URL [$BLACKLIST]"
                        exit 1
                    fi
                done
            fi
        done
    fi
fi

exit 0
