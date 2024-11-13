import helpers.billing

from customers.models import Customer
from subscriptions.models import UserSubscription, Subscription


def clear_dangling_subscriptions():
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
                

def sync_subscription_group_permissions():
    # So subscription model handles permissions
    qs = Subscription.objects.filter(active=True)
    for obj in qs:
        subscription_permissions = obj.permissions.all()
        for group in obj.groups.all():
            group.permissions.set(subscription_permissions)