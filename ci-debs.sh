#!/bin/bash

set -eux

# List latest ci-int debs

curl -s 'https://rick-harding+guibot:ShjSZ4csTp9g3PmrFX5b@private-ppa.launchpad.net/rick-harding+guibot/ci-int/ubuntu/dists/trusty/main/binary-amd64/Packages.bz2' | bzgrep -E 'Package|Version'
