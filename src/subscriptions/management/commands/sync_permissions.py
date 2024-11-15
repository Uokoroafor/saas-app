from typing import Any
from django.core.management.base import BaseCommand

from subscriptions.models import Subscription

import utils as sub_utils


class Command(BaseCommand):

    def handle(self, *args: Any, **options: Any) -> str | None:
        sub_utils.sync_subscription_group_permissions()
