from typing import Any
from django.core.management.base import BaseCommand

from subscriptions.models import Subscription


class Command(BaseCommand):

    def handle(self, *args: Any, **options: Any) -> str | None:
        # So subscription model handles permissions
        qs = Subscription.objects.filter(active=True)
        for obj in qs:
            subscription_permissions = obj.permissions.all()
            for group in obj.groups.all():
                group.permissions.set(subscription_permissions)