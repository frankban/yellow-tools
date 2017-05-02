#!/bin/bash

set -eux

juju set-model-config enable-os-refresh-update=false
juju set-model-config enable-os-upgrade=false
