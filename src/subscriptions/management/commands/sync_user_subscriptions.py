from typing import Any
from django.core.management.base import BaseCommand, CommandParser

import subscriptions.utils as subs_utils


class Command(BaseCommand):
    """Management command to process subscriptions with various filtering options.

    This command provides arguments to manage subscriptions, such as clearing dangling
    subscriptions, enabling verbose output, and filtering based on date ranges or user status.
    """

    def add_arguments(self, parser: CommandParser):
        """Defines command-line arguments for the subscription management command.

        Args:
            parser (CommandParser): The parser for command-line arguments.
        """
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
        super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> None:
        """Handles the subscription synchronization and cleanup process.

        This method processes command-line options to either clear dangling subscriptions
        or refresh active user subscriptions based on various filters such as date ranges
        and user status.

        Args:
            *args (Any): Positional arguments passed to the command.
            **options (Any): Keyword arguments containing command-line options.

        Returns:
            None: This method does not return a value.
        """
        clear_dangling = options.get("clear_dangling")
        verbose = options.get("verbose")
        all_users = not options.get("all_users")

        # It's a fiddle but it makes sense. If all users is True, active only is False.
        days_since = options.get("days_since")
        days_remaining = options.get("days_remaining")
        from_days = options.get("from_days")
        to_days = options.get("to_days")

        if clear_dangling:
            # Clearing Active Subs not in use...
            subs_utils.clear_dangling_subscriptions()
            self.stdout.write(
                self.style.SUCCESS("Cleared dangling subscriptions.")
            )
        else:
            # Syncing Active Subs...
            done = subs_utils.refresh_active_users_subscriptions(
                verbose=verbose,
                active_only=all_users,
                days_remaining=days_remaining,
                days_since=days_since,
                from_days=from_days,
                to_days=to_days,
            )
            if done:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Successfully refreshed active subscriptions."
                    )
                )
        return
