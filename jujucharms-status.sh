#!/bin/bash

# Check the status on many microservices.
# Usage: jujucharmstatus.sh [domain]
# If domain is blank then production is used.

set -eux
protocol="https"
prefix=""
if [[ -z "$@" ]]; then
    domain="jujucharms.com"
elif [[ $1 == "staging" ]]; then
    domain="staging.jujucharms.com"
elif [[ $1 == "guimaas" ]]; then
    domain="jujugui.org"
    prefix="www."
else
    exit
fi
   
http $protocol://$prefix$domain/_version
http $protocol://api.$domain/identity/debug/info
http $protocol://api.$domain/identity/debug/status
http $protocol://api.$domain/jem/debug/info
http $protocol://api.$domain/jem/debug/status
http $protocol://demo.$domain/version
http $protocol://api.$domain/charmstore/debug/info
http $protocol://api.$domain/charmstore/v5/debug/status
