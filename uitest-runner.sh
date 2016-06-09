#!/bin/bash

set -eux

# Create $HOME/.uitest-creds with:

#credentials=LPUSERNAME:LPPASSWORD
#admin=admin:ADMINPASSWORD

. $HOME/.uitest-creds

case $1 in
    production)
	url='https://jujucharms.com'
	;;
    staging)
	url='https://staging.jujucharms.com'
	;;
    guimaas | jujugui.org)
	url='https://www.jujugui.org'
	;;
    *)
	url=http://$1
	;;
esac

if [ "$#" -ge 2 ]; then
    test=$2
else
    test=''
fi

#devenv/bin/uitest  --url $url --credentials $credentials --admin $admin -c lxd --debug $test
devenv/bin/uitest  --url $url --credentials $credentials --admin $admin -c lxd $test
