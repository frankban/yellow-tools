#!/usr/bin/env python3

"""List EC2 instances and volumes currently in use.

To use this, you must "pip3 install boto" first.
"""

import argparse
from collections import namedtuple
from concurrent import futures
import logging
import os
import re
import sys

from boto import (
    ec2,
    exception as ec2_exceptions,
)


# How many times a connection is retried.
RETRY_TIMES = 5
# Terminated instances can be ignored.
TERMINATED_STATE = 'terminated'
# Unicode fun.
instance_icon = '\U0001F5F2'
volume_icon = '\U0001F4BE'


# Define EC2 instance and volume types.
Instance = namedtuple('Instance', 'id dns state')
Volume = namedtuple('Volume', 'id size state')


def get_credentials():
    """Retrieve AWS credentials from ~/.ec2/aws_id."""
    path = os.path.expanduser('~/.ec2/aws_id')
    try:
        lines = [line.strip() for line in open(path)]
    except IOError:
        raise IOError('unable to find AWS credentials at {}'.format(path))
    access_key, secret_key = filter(None, lines)
    return access_key, secret_key


def get_regions(pattern):
    """Fetch and return AWS regions, excluding non-relevant ones.

    Also exclude the ones whose name does not match the given pattern.
    """
    return [
        region for region in ec2.regions()
        if not region.name.startswith('cn-') and
        not region.name.startswith('us-gov-') and
        re.search(pattern, region.name) is not None
    ]


def retry(func, times=RETRY_TIMES):
    """Retry the given function for the given times.

    The function is retried in case of a AWS connection error.
    Return the function result or None if the function fails.
    """
    for _ in range(RETRY_TIMES):
        try:
            result = func()
        except ec2_exceptions.EC2ResponseError as err:
            # Sometimes the connection fails, for reasons.
            logging.warn(err)
            continue
        return result
    return None


def get_instances(conn):
    """Get EC2 instances information for the given connection.

    Return None if connection problems prevents from fetching results.
    """
    instances = []
    reservations = retry(conn.get_all_instances)
    if reservations is None:
        return None
    for reservation in reservations:
        for instance in reservation.instances:
            if instance.state != TERMINATED_STATE:
                instances.append(Instance(
                    id=instance.id,
                    dns=instance.dns_name or 'no dns name',
                    state=instance.state,
                ))
    return instances


def get_volumes(conn):
    """Get volumes information for the given connection.

    Return None if connection problems prevents from fetching results.
    """
    volumes = retry(conn.get_all_volumes)
    if volumes is None:
        return None
    return [Volume(
        id=volume.id,
        size='{} GiB'.format(volume.size),
        state=volume.status,
    ) for volume in volumes]


def fetch_region_data(region, access_key, secret_key):
    """Fetch instances and volumes from the given AWS region."""
    conn = region.connect(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key)
    instances = get_instances(conn)
    volumes = get_volumes(conn)
    conn.close()
    return region.name, instances, volumes


def report(region_name, instances, volumes):
    """Print information about collected instances and volumes."""
    if instances is None:
        print(red('error: unable to fetch instances'))
        instances = []
    if volumes is None:
        print(red('error: unable to fetch volumes'))
        volumes = []
    msg = '{}: {} instances, {} volumes'.format(
        region_name, len(instances), len(volumes))
    print(blue(msg))
    for instance in instances:
        print('{0} instance {1.id}:\n  {1.dns}\n  {1.state}'.format(
            instance_icon, instance))
    for volume in volumes:
        print('{0} volume {1.id}:\n  {1.size}\n  {1.state}'.format(
            volume_icon, volume))


def blue(text):
    return '\033[01;34m{}\033[00m'.format(text)


def red(text):
    return '\033[01;31m{}\033[00m'.format(text)


def setup():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'region', default='', nargs='?',
        help='optionally only include regions matching the given string')
    parser.add_argument('--access', default=None, help='the AWS access key')
    parser.add_argument('--secret', default=None, help='the AWS secret key')
    return parser.parse_args()


def main():
    """Start the script."""
    options = setup()
    access_key, secret_key = options.access, options.secret
    if not (access_key and secret_key):
        access_key, secret_key = get_credentials()
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        fs = [
            executor.submit(fetch_region_data, region, access_key, secret_key)
            for region in get_regions(options.region)
        ]
        for future in futures.as_completed(fs):
            report(*future.result())


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('quitting')
    except Exception as err:
        sys.exit(err)
