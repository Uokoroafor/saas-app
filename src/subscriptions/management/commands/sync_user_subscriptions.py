from typing import Any
from django.core.management.base import BaseCommand

import subscriptions.utils as subs_utils


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--clear-dangling", action="store_true", default=False)
        return super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> str | None:
        clear_dangling = options.get("clear_dangling")
        if clear_dangling:
            print("Clearing Active Subs not in use...")
            subs_utils.clear_dangling_subscriptions()
            print("Done!")
        else:
            print("Syncing Active Subs")
            print("Done!")