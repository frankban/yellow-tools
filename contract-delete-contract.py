#!/usr/bin/env python3

import argparse
import subprocess


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
    "contract_items",
    "resource_access",
)


def run_contract(cmd, *args):
    """Run the contract CLI with the given subcommnd and args."""
    command = ("contract", cmd) + tuple(args)
    return subprocess.check_output(command).decode("utf-8")


def get_delete_queries(id):
    """Return a list of queries to be run to delete a contract with the given id."""
    queries = [f"DELETE FROM {table} WHERE contract_id = '{id}';" for table in CONTRACT_RELATED_TABLES]
    queries.append(f"DELETE FROM contracts WHERE id = '{id}';")
    return queries


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="id of the contract to delete, either encoded or decoded")
    return parser.parse_args()


def main(contract_id):
    if contract_id.startswith("c"):
        contract_id = run_contract("decode-id", contract_id).strip().strip("'")
    queries = get_delete_queries(contract_id)
    print("\n".join(queries))


if __name__ == "__main__":
    args = setup()
    main(args.id)
