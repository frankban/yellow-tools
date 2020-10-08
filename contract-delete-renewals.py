#!/usr/bin/env python3

import argparse
import collections
import datetime
import json
import operator
import subprocess
import sys


# Renewal represents a renewal in ua-contracts.
Renewal = collections.namedtuple(
    "Renewal", "id encoded_id status actionable start end contract_id sf_asset_id products account_id account_name sf_account_id")


def run_contract(cmd, *args):
    """Run the contract CLI with the given subcommnd and args."""
    command = ("contract", cmd) + tuple(args)
    return subprocess.check_output(command).decode("utf-8")


def get_renewals(ids):
    """Generate renewal objects from the given decoded ids."""
    ids_len = len(ids)
    for num, id in enumerate(ids):
        print(f"{num}/{ids_len}", end="\r", file=sys.stderr)
        encoded_id = run_contract("encode-id", "r", id).strip()
        out = run_contract("show-renewal", encoded_id, "--format", "json")
        info = json.loads(out)
        contract_id = info["contractID"]
        out = run_contract("show-contract", contract_id, "--format", "json")
        account_contract_info = json.loads(out)
        contract_info, account_info = account_contract_info["contractInfo"], account_contract_info["accountInfo"]
        yield Renewal(
            id=id,
            encoded_id=info["id"],
            status=info["status"],
            actionable=info.get("actionable", False),
            start=_parse_datetime(info["start"]),
            end=_parse_datetime(info["end"]),
            contract_id=contract_id,
            sf_asset_id=_parse_sf_ids(info["externalAssetIDs"]),
            products=contract_info['products'],
            account_id=account_info["id"],
            account_name=account_info["name"],
            sf_account_id=_parse_sf_ids(account_info["externalAccountIDs"][0]),
        )


def _parse_datetime(value):
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")


def _parse_sf_ids(value):
    if value is None or value["origin"] != "Salesforce":
        return ""
    return ", ".join(value["IDs"])


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file", type=argparse.FileType("r"),
        help="name of a file containing a list of renewal ids separated by newlines")
    return parser.parse_args()


def main(file):
    counter = collections.Counter()
    ids = set(line.strip() for line in file)
    for r in get_renewals(ids):
        verb = "actionable" if r.actionable else "not actionable"
        products = ", ".join(sorted(r.products))

        counter["total"] += 1
        counter[verb] += 1
        counter[r.status] += 1
        for product in r.products:
            counter[product] += 1

        print(f"\n# Delete {r.status} renewal {r.id}")
        print(f"# (salesforce asset {r.sf_asset_id})")
        print(f"# {verb} from {r.start} till {r.end}")
        print(f"# for contract {r.contract_id} ({products})")
        print(f"# owned by {r.account_name} ({r.account_id})")
        print(f"# (salesforce account {r.sf_account_id})")
        print(f"contract delete-renewal {r.encoded_id}")

    print("\ncounts:")
    for key, value in counter.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    args = setup()
    main(args.file)
