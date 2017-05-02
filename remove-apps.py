#!/usr/bin/python3

import json
import subprocess
from pprint import pprint


def find_apps():
    cmd = 'juju status --format=json'.split()
    status = subprocess.check_output(cmd)
    status = status.decode('utf-8')
    jout = json.loads(str(status))
    return jout['applications'].keys()


def remove_apps(apps):
    template = 'juju remove-application -B {}'
    for app in apps:
        cmd = template.format(app)
        print(cmd)
        subprocess.call(cmd.split())

if __name__ == '__main__':
    apps = find_apps()
    remove_apps(apps)
