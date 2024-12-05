from typing import Any
from django.core.management.base import BaseCommand


import utils as sub_utils


class Command(BaseCommand):
    """Management command to synchronise subscription group permissions.

    This command calls a utility function to sync permissions for subscription groups.
    """

    def handle(self, *args: Any, **options: Any) -> None:
        """Executes the sync_subscription_group_permissions function.

        Args:
            *args (Any): Positional arguments passed to the command.
            **options (Any): Keyword arguments passed to the command.

        Returns:
            None: This method does not return a value.
        """
        sub_utils.sync_subscription_group_permissions()
        return
