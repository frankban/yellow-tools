#!/usr/bin/env python3

"""Compare packages in the provided PPAs."""

# This script requires python3 and the requests package to be installed.

import argparse
from collections import namedtuple
import gzip
from html import parser as html_parser
import logging

import requests


Package = namedtuple('Package', 'name path version arch sha')
Diff = namedtuple('Diff', 'num_source num_target added removed changed')
_DEFAULT_SUITES = [
    'precise',
    'trusty', 'trusty-infra-security', 'trusty-infra-updates',
    'xenial', 'xenial-infra-security', 'xenial-infra-updates',
    'bionic', 'bionic-infra-security', 'bionic-infra-updates',
]


class _HTMLParser(html_parser.HTMLParser):
    """Parse HTML links."""
    def __init__(self):
        super().__init__()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            link = dict(attrs).get('href')
            if link:
                self.links.add(link)


def _get_links(url):
    """Return href links included in the HTML document at the given URL."""
    resp = requests.get(url)
    resp.raise_for_status()
    parser = _HTMLParser()
    parser.feed(resp.text)
    return parser.links


def get_packages(url, arches=None, suites=None):
    """Return a set of all binary packages in the PPA at the given URL.

    If an arches sequence is provided, it is used to filter by architecture.
    If a suites sequence is provided, it is used to filter by suite.
    """
    if suites is None:
        suites = _DEFAULT_SUITES
    packages = set()
    dists_url = url + 'dists/'
    logging.debug(f'fetching packages: {dists_url}')
    dist_links = _get_links(dists_url)
    for dist_link in dist_links:
        if dist_link.rstrip('/') in suites:
            dist_url = dists_url + dist_link + 'main/'
            logging.debug(f'fetching packages: {dist_url}')
            arch_links = _get_links(dist_url)
            for arch_link in arch_links:
                if arch_link.startswith('binary'):
                    arch_packages = _extract(dist_url + arch_link + 'Packages.gz', arches)
                    packages.update(arch_packages)
    return packages


def _extract(url, arches):
    """Uncompress the Packages.gz resource at the given URL and extract included packages."""
    logging.debug(f'extracting: {url}')
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    packages = set()
    file = gzip.GzipFile(mode='r', fileobj=resp.raw)
    name = path = version = arch = sha = ''
    for line in file:
        line = line.decode('utf8').strip()
        if line.startswith('Package: '):
            name = line.split()[1]
        if line.startswith('Filename: '):
            path = line.split()[1]
        if line.startswith('Version: '):
            version = line.split()[1]
        if line.startswith('Architecture: '):
            arch = line.split()[1]
        if line.startswith('SHA256: '):
            sha = line.split()[1]
        if not line:
            if (arches is None) or (arch in arches):
                packages.add(Package(name, path, version, arch, sha))
            name = path = version = arch = sha = ''
    return packages


def compare(packages1, packages2):
    """Compare two sets of package objects and produce a Diff."""
    num_source, num_target = len(packages1), len(packages2)
    common = packages1 & packages2
    packages1 -= common
    packages2 -= common
    paths1 = {package.path for package in packages1}
    paths2 = {package.path for package in packages2}
    common = paths1 & paths2
    dict1 = {package.path: package for package in packages1}
    dict2 = {package.path: package for package in packages2}
    changed = []
    for path in common:
        changed.append((dict1.pop(path), dict2.pop(path)))
    return Diff(
        num_source=num_source,
        num_target=num_target,
        added=tuple(sorted(dict2.values())),
        removed=tuple(sorted(dict1.values())),
        changed=tuple(sorted(changed)),
    )


def report(diff):
    """Report information included in the diff."""
    if diff.added:
        print(f'+ {len(diff.added)} added')
        for package in diff.added:
            print(f'+ {package.path}')
            print(f'  {package.name} {package.version} ({package.arch})')
    if diff.removed:
        print(f'- {len(diff.removed)} removed')
        for package in diff.removed:
            print(f'- {package.path}')
            print(f'  {package.name} {package.version} ({package.arch})')
    if diff.changed:
        print(f'* {len(diff.changed)} changed')
        for package1, package2 in diff.changed:
            print(f'* {package1.path}')
            print(f'  - {package1.name} {package1.version} ({package1.arch})')
            print(f'    {package1.sha}')
            print(f'  + {package2.name} {package2.version} ({package2.arch})')
            print(f'    {package2.sha}')
    print(f'source: {diff.num_source} | target: {diff.num_target}')


def _ppa_url(value):
    """Validate that the given value is a valid URL.

    Return a cleaned up value ensuring it ends with "/ubuntu/".
    Raise an ArgumentTypeError if the value is not valid.
    """
    if not (value.startswith('http://') or value.startswith('https://')):
        raise argparse.ArgumentTypeError(f'provided ppa {value} is not a valid URL')
    value = value.rstrip('/')
    if not value.endswith('/ubuntu'):
        value += '/ubuntu'
    return value + '/'


def _setup():
    """Set up logging and argument parser."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('ppa1', help='URL of the first PPA', type=_ppa_url)
    parser.add_argument('ppa2', help='URL of the second PPA', type=_ppa_url)
    parser.add_argument(
        '--arches', nargs='+', help='A space separated list of architectures to retrieve (by default all are fetched)')
    parser.add_argument(
        '--suites', nargs='+',
        help='A space separated list of suites to retrieve if present in the PPA\n(defaulting to all known suites)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    logging.basicConfig(
        datefmt='%Y-%m-%d %H:%M:%S',
        format='%(asctime)s %(levelname)s:\t%(message)s',
        level=logging.DEBUG if args.verbose else logging.INFO)
    return args


def _run(args):
    """Run the command."""
    packages1 = get_packages(args.ppa1, arches=args.arches, suites=args.suites)
    packages2 = get_packages(args.ppa2, arches=args.arches, suites=args.suites)
    diff = compare(packages1, packages2)
    report(diff)


if __name__ == '__main__':
    args = _setup()
    _run(args)
