from typing import Any
from django.core.management.base import BaseCommand

import subscriptions.utils as subs_utils


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-dangling",
            action="store_true",
            default=False,
            help="Clears dangling subscriptions (default: False).",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose output (default: False).",
        )
        parser.add_argument(
            "--all-users",
            action="store_true",
            default=False,
            help="Process all users (not just active only) (default: False).",
        )
        return super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> str | None:
        clear_dangling = options.get("clear_dangling")
        verbose = options.get("verbose")
        all_users = not options.get(
            "all_users"
        )  # It's a fiddle but it makes sense. If all users is True, active only is False.
        if clear_dangling:
            print("Clearing Active Subs not in use...")
            subs_utils.clear_dangling_subscriptions()
            print("Done!")
        else:
            print("Syncing Active Subs")
            done = subs_utils.refresh_active_users_subscriptions(
                verbose=verbose, active_only=all_users
            )  # active_only = True
            if done:
                print("Done!")
