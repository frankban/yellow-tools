#!/usr/bin/env python3

import argparse
import collections
import datetime
import json
import operator
import subprocess
import sys


# Contract represents a contract in ua-contracts.
Contract = collections.namedtuple("Contract", "id encoded_id effective_to products account_id account_name")

# Define contract related tables.
CONTRACT_RELATED_TABLES = (
    "contract_tokens",
    "contract_products",
    "contract_affordances",
    "contract_allowances",
    "contract_directives",
    "contract_obligations",
    "contract_external_asset_ids",
    "contract_machines",
    "resource_access",
)

now = datetime.datetime.now()


def run_contract(cmd, *args):
    """Run the contract CLI with the given subcommnd and args."""
    command = ("contract", cmd) + tuple(args)
    return subprocess.check_output(command).decode("utf-8")


def get_account_contracts(ids):
    """Return a dictionary mapping account ids to contracts with the given ids."""
    account_contracts = {}
    ids_len = len(ids)
    for num, id in enumerate(ids):
        print(f"{num}/{ids_len}", end="\r", file=sys.stderr)
        encoded_id = run_contract("encode-id", "c", id).strip()
        out = run_contract("show-contract", encoded_id, "--format", "json")
        info = json.loads(out)
        contract_info, account_info = info["contractInfo"], info["accountInfo"]
        effective_to = contract_info.get("effectiveTo")
        if effective_to is not None:
            try:
                effective_to = datetime.datetime.strptime(effective_to, "%Y-%m-%dT%H:%M:%S.%f%z")
            except ValueError:
                effective_to = datetime.datetime.strptime(effective_to, "%Y-%m-%dT%H:%M:%S%z")
            effective_to = effective_to.replace(tzinfo=None)
        contract = Contract(
            id=id,
            encoded_id=contract_info["id"],
            effective_to=effective_to,
            products=", ".join(sorted(contract_info['products'])),
            account_id=account_info["id"],
            account_name=account_info["name"],
        )
        key = (contract.account_id, contract.products)
        account_contracts.setdefault(key, []).append(contract)
    return account_contracts


def split_contracts(account_contracts):
    """Return lists of contracts to keep, to be deleted and problematic contracts from the given map."""
    to_keep, to_delete, not_expiring, multiple_effective = [], [], [], []
    for contracts in account_contracts.values():
        _split_contracts(contracts, to_keep, to_delete, not_expiring, multiple_effective)
    return to_keep, to_delete, not_expiring, multiple_effective


def _split_contracts(contracts, to_keep, to_delete, not_expiring, multiple_effective):
    to_process = []
    for contract in contracts:
        if contract.effective_to is None:
            not_expiring.append(contract)
            continue
        to_process.append(contract)
    to_process = sorted(to_process, key=operator.attrgetter("effective_to"))
    while len(to_process) > 1:
        if to_process[0].effective_to >= now:
            multiple_effective.extend(to_process)
            return
        to_delete.append(to_process.pop(0))
    to_keep.extend(to_process)


def get_delete_queries(id):
    """Return a list of queries to be run to delete a contract with the given id."""
    queries = [f"DELETE FROM {table} WHERE contract_id = '{id}';" for table in CONTRACT_RELATED_TABLES]
    queries.append(f"DELETE FROM contracts WHERE id = '{id}';")
    return queries


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file", type=argparse.FileType("r"),
        help="name of a file containing a list of contract ids separated by newlines")
    return parser.parse_args()


def main(file):
    ids = [line.strip() for line in file]
    account_contracts = get_account_contracts(ids)
    to_keep, to_delete, not_expiring, multiple_effective = split_contracts(account_contracts)

    if not_expiring:
        print("\n* problematic contracts, never expiring:\n")
        for contract in not_expiring:
            print(f"- {contract.products} {contract.encoded_id}")
            print(f"  {contract.id}")
            print(f"  owned by {contract.account_name} ({contract.account_id})")

    if multiple_effective:
        print("\n* problematic contracts, multiple effective for the same account and product:\n")
        for contract in multiple_effective:
            print(f"- {contract.products} {contract.encoded_id}")
            print(f"  {contract.id}")
            print(f"  effective to {contract.effective_to}")
            print(f"  owned by {contract.account_name} ({contract.account_id})")

    if to_keep:
        print("\n* contracts to keep:\n")
        for contract in to_keep:
            print(f"- {contract.products} {contract.encoded_id}")
            print(f"  {contract.id}")
            print(f"  effective to {contract.effective_to}")
            print(f"  owned by {contract.account_name} ({contract.account_id})")

    if not to_delete:
        print("no contracts to delete")
        return

    print("\n* contracts to delete:\n")
    for contract in to_delete:
        print(contract.encoded_id)

    print("\n* queries:\n")
    print("-- Queries are generated by running the script at")
    print("-- https://github.com/frankban/yellow-tools/blob/master/delete-queries.py")
    for contract in to_delete:
        print(f"\n-- Delete {contract.products} contract {contract.encoded_id}")
        print(f"-- owned by {contract.account_id} effective to {contract.effective_to}")
        queries = get_delete_queries(contract.id)
        print("\n".join(queries))


if __name__ == "__main__":
    args = setup()
    main(args.file)
