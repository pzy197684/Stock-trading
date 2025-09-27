"""
Simple CLI helpers for PlatformManager: list/create/delete platform instances for accounts.
This is intentionally minimal and meant for developer/ops usage.
"""
from typing import Optional
import argparse
from core.managers.platform_manager import PlatformManager

_pm = PlatformManager()


def main():
    parser = argparse.ArgumentParser(prog="platform_cli")
    sub = parser.add_subparsers(dest="cmd")

    parser_list = sub.add_parser("list")
    parser_list.add_argument("--account", required=False)

    parser_create = sub.add_parser("create")
    parser_create.add_argument("account")
    parser_create.add_argument("platform")
    parser_create.add_argument("--api_key", required=False)
    parser_create.add_argument("--api_secret", required=False)

    parser_delete = sub.add_parser("delete")
    parser_delete.add_argument("account")
    parser_delete.add_argument("platform")

    args = parser.parse_args()
    if args.cmd == "list":
        if args.account:
            print(_pm.list_platforms(account=args.account))
        else:
            print(_pm.list_platforms())
    elif args.cmd == "create":
        try:
            inst = _pm.create_platform_for_account(args.account, args.platform, api_key=args.api_key, api_secret=args.api_secret)
            print(f"Created: account={args.account} platform={args.platform} -> {inst}")
        except Exception as e:
            print(f"Error: {e}")
    elif args.cmd == "delete":
        try:
            # simple delete
            _pm.platforms.get(args.account, {}).pop(args.platform, None)
            print(f"Deleted: account={args.account} platform={args.platform}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
