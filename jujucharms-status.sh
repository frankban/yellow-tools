#!/bin/bash

# Check the status on many microservices.
# Usage: jujucharmstatus.sh [domain]
# If domain is blank then production is used.

set -eux
protocol="https"
prefix=""
api="api"
if [[ -z "$@" ]]; then
    domain="jujucharms.com"
elif [[ $1 == "staging" ]]; then
    domain="staging.jujucharms.com"
elif [[ $1 == "jujugui.org" ]]; then
    domain="jujugui.org"
    prefix="www."
    api="www"
else
    exit
fi
   
http $protocol://$prefix$domain/_version
http $protocol://$api.$domain/identity/debug/info
http $protocol://$api.$domain/identity/debug/status
http $protocol://$api.$domain/bundleservice/debug/info
http $protocol://demo.$domain/static/gui/build/app/version.json
http $protocol://$api.$domain/charmstore/debug/info
http $protocol://$api.$domain/charmstore/v5/debug/status
