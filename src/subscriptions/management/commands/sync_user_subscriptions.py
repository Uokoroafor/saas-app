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
        parser.add_argument(
            "--days-remaining",
            default=0,
            help="Number of days left until the current period end of the subscription",
            type=int,
        )
        parser.add_argument(
            "--days-since",
            default=0,
            help="Number of days since the end of the subscription",
            type=int,
        )

        parser.add_argument(
            "--from-days",
            default=0,
            help="Number of days from now for a date range filter start date",
            type=int,
        )

        parser.add_argument(
            "--to-days",
            default=0,
            help="Number of days from now for a date range filter end date",
            type=int,
        )
        return super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> str | None:
        clear_dangling = options.get("clear_dangling")
        verbose = options.get("verbose")
        all_users = not options.get(
            "all_users"
        )  # It's a fiddle but it makes sense. If all users is True, active only is False.
        days_since = options.get("days_since")
        days_remaining = options.get("days_remaining")
        from_days = options.get("from_days")
        to_days = options.get("to_days")

        if clear_dangling:
            # print("Clearing Active Subs not in use...")
            subs_utils.clear_dangling_subscriptions()
            # print("Done!")
        else:
            # print("Syncing Active Subs")
            done = subs_utils.refresh_active_users_subscriptions(
                verbose=verbose,
                active_only=all_users,
                days_remaining=days_remaining,
                days_since=days_since,
                from_days=from_days,
                to_days=to_days,
            )  # active_only = True
            if done:
                print("Done!")
