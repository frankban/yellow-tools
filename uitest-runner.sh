#!/bin/bash

set -eux

# Create $HOME/.uitest-creds with:

#credentials=LPUSERNAME:LPPASSWORD
#admin=admin:ADMINPASSWORD

. $HOME/.uitest-creds

case $1 in
    production)
	url='--url https://jujucharms.com'
	;;
    staging)
	url='--url https://staging.jujucharms.com'
	;;
    qa | jujugui.org)
	url=''
	;;
    *)
	url='--url http://$1'
	;;
esac

if [ "$#" -ge 2 ]; then
    test=$2
else
    test=''
fi

debug=''
phantom=''
#debug="--debug"
#phantom="--driver phantom"

devenv/bin/uitest  $url --credentials $credentials --admin $admin -c lxd $debug $phantom $test
