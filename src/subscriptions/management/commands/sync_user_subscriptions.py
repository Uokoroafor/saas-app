from typing import Any
from django.core.management.base import BaseCommand
import helpers.billing

from customers.models import Customer
from subscriptions.models import UserSubscription


class Command(BaseCommand):

    def handle(self, *args: Any, **options: Any) -> str | None:
        # So subscription model handles permissions
        qs = Customer.objects.filter(stripe_id__isnull=False)
        for customer_obj in qs:
            user = customer_obj.user
            
            customer_stripe_id = customer_obj.stripe_id
            print(f"Sync {user}'s ({customer_stripe_id}) subscriptions and remove old ones")
            subscriptions=helpers.billing.get_customer_active_subscriptions(customer_stripe_id)
            for sub in subscriptions:
                existing_user_subs_qs = UserSubscription.objects.filter(stripe_id__iexact=f"{sub.id}".strip())
                if not existing_user_subs_qs.exists():
                    print(sub.id, existing_user_subs_qs.exists())
                    helpers.billing.cancel_subscription(stripe_id=sub.id,
                                                        reason="Dangling Active Subscription",
                                                        cancel_at_period_end=True)