#!/usr/bin/env python3

import argparse
import subprocess


# Define account related tables.
ACCOUNT_RELATED_TABLES = (
    "contracts",
    "account_access",
    "account_external_ids",
    "purchases",
    "subscriptions",
    "temporary_account_tokens",
)


def run_contract(cmd, *args):
    """Run the contract CLI with the given subcommnd and args."""
    command = ("contract", cmd) + tuple(args)
    return subprocess.check_output(command).decode("utf-8")


def get_delete_queries(id, delete_users):
    """Return a list of queries to be run to delete an account with the given id."""
    queries = [
        f"DELETE FROM subscriptions_external_subscription_ids WHERE subscription IN (SELECT id FROM subscriptions WHERE account_id = '{id}');",
        f"DELETE FROM purchase_items WHERE purchase_id IN (SELECT id FROM purchases WHERE account_id = '{id}');",
    ]
    if delete_users:
        queries.append(f"DELETE FROM users WHERE id IN (SELECT user_id FROM account_access WHERE account_id = '{id}');")
    queries.extend(f"DELETE FROM {table} WHERE account_id = '{id}';" for table in ACCOUNT_RELATED_TABLES)
    queries.append(f"DELETE FROM accounts WHERE id = '{id}';")
    return queries


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="id of the account to delete, either encoded or decoded")
    parser.add_argument("--delete-users", action="store_true", help="whether to generate queries for deleting users")
    return parser.parse_args()


def main(account_id, delete_users):
    if account_id.startswith("a"):
        account_id = run_contract("decode-id", account_id).strip().strip("'")
    queries = get_delete_queries(account_id, delete_users)
    print("\n".join(queries))


if __name__ == "__main__":
    args = setup()
    main(args.id, args.delete_users)
