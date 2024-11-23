from typing import List, Optional
import helpers.billing

from customers.models import Customer
from subscriptions.models import UserSubscription, Subscription, SubscriptionStatus
from django.db.models import Q


def refresh_active_users_subscriptions(
    user_ids: Optional[List | str | int] = None,
    active_only=True,
    verbose=False,
    days_remaining=0,
    days_since=0,
    from_days=0,
    to_days=0,
):
    
    qs = (
        UserSubscription.objects.all()
        if not active_only
        else UserSubscription.objects.all().by_active_trialling()
    )
    if user_ids is not None:
        qs = qs.by_user_ids(user_ids=user_ids)

    if days_since > 0:
        qs = qs.by_days_since(days_since)

    if days_remaining > 0:
        qs = qs.by_days_remaining(days_remaining)

    if from_days < to_days:
        qs = qs.by_days_range(from_days=from_days, to_days=to_days)
    else:
        pass
        # TODO Add warnings if from_days exceeds end_days

    qs_count, complete = qs.count(), 0
    for obj in qs:
        if verbose:
            print(
                f"Refreshing {obj.user} - Subscription [{obj.subscription}] - End Date [{obj.current_period_end}]"
            )
        if obj.stripe_id:
            sub_data = helpers.billing.get_subscription(obj.stripe_id)
            for k, v in sub_data.items():
                setattr(obj, k, v)
            obj.save()
            complete += 1
    return complete == qs_count


def convert_user_ids_to_list(user_ids: Optional[List | str | int]):
    if user_ids is None:
        return []
    elif isinstance(user_ids, list):
        return user_ids
    elif isinstance(user_ids, int):
        return [user_ids]
    elif isinstance(user_ids, str):
        return [user_ids]


def clear_dangling_subscriptions():
    # So subscription model handles permissions
    qs = Customer.objects.filter(stripe_id__isnull=False)
    for customer_obj in qs:
        user = customer_obj.user

        customer_stripe_id = customer_obj.stripe_id
        print(f"Sync {user}'s ({customer_stripe_id}) subscriptions and remove old ones")
        subscriptions = helpers.billing.get_customer_active_subscriptions(
            customer_stripe_id
        )
        for sub in subscriptions:
            existing_user_subs_qs = UserSubscription.objects.filter(
                stripe_id__iexact=f"{sub.id}".strip()
            )
            if not existing_user_subs_qs.exists():
                print(sub.id, existing_user_subs_qs.exists())
                helpers.billing.cancel_subscription(
                    stripe_id=sub.id,
                    reason="Dangling Active Subscription",
                    cancel_at_period_end=True,
                )


def sync_subscription_group_permissions():
    # So subscription model handles permissions
    qs = Subscription.objects.filter(active=True)
    for obj in qs:
        subscription_permissions = obj.permissions.all()
        for group in obj.groups.all():
            group.permissions.set(subscription_permissions)
