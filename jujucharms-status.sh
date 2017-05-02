#!/bin/bash

# Check the status on many microservices.
# Usage: jujucharmstatus.sh [domain]
# If domain is blank then production is used.

set -eux
protocol="https"
prefix=""
verify=""
if [[ -z "$@" ]]; then
    domain="jujucharms.com"
elif [[ $1 == "staging" ]]; then
    domain="staging.jujucharms.com"
elif [[ $1 == "qa" ]]; then
    protocol="https"
    domain="jujugui.org"
    prefix="www."
    verify="--verify yes"
else
    exit
fi

http $verify $protocol://$prefix$domain/_version
http $verify $protocol://api.$domain/identity/debug/info
http $verify $protocol://api.$domain/identity/debug/status
http $verify $protocol://jimm.$domain/debug/info
http $verify $protocol://jimm.$domain/debug/status
#http $verify $protocol://demo.$domain/version
http $verify $protocol://api.$domain/charmstore/debug/info
http $verify $protocol://api.$domain/charmstore/v5/debug/status
