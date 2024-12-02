from typing import List, Optional, Union
import helpers.billing

from customers.models import Customer
from subscriptions.models import UserSubscription, Subscription
import warnings
import logging

logger = logging.getLogger("myproject")


def refresh_active_users_subscriptions(
    user_ids: Optional[Union[List[int], str, int]] = None,
    active_only: bool = True,
    verbose: bool = False,
    days_remaining: int = 0,
    days_since: int = 0,
    from_days: int = 0,
    to_days: int = 0,
) -> bool:
    """Refreshes active user subscriptions by updating their data from Stripe.

    This function retrieves and updates user subscriptions based on various filters, such as
    user IDs, active status, and date ranges. It fetches subscription data from Stripe and
    updates local records accordingly.

    Args:
        user_ids (Optional[Union[List[int], str, int]]): A list, single ID, or string
            representing user IDs to filter subscriptions. If `None`, all users are considered.
        active_only (bool): If `True`, only active or trialing subscriptions are processed.
            Defaults to `True`.
        verbose (bool): If `True`, prints detailed output for each subscription processed.
            Defaults to `False`.
        days_remaining (int): Filters subscriptions with this many days remaining until
            the current period ends. Defaults to `0`.
        days_since (int): Filters subscriptions that ended this many days ago. Defaults to `0`.
        from_days (int): The starting point (in days from now) for filtering subscriptions
            by date range. Defaults to `0`.
        to_days (int): The endpoint (in days from now) for filtering subscriptions by date
            range. Defaults to `0`.

    Returns:
        bool: `True` if all subscriptions are successfully refreshed, `False` otherwise.
    """
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
    elif from_days >= to_days and not (from_days == 0 and to_days == 0):
        msg = f"'from_days' ({from_days}) should be less than 'to_days' ({to_days}). Skipping days filtering."
        warnings.warn(msg, RuntimeWarning)
        logging.warning(msg)
    qs_count, complete = qs.count(), 0
    for obj in qs:
        msg = f"Refreshing {obj.user} - Subscription [{obj.subscription}] - End Date [{obj.current_period_end}]"
        logging.info(msg)
        if verbose:
            print(msg)
        if obj.stripe_id:
            sub_data = helpers.billing.get_subscription(obj.stripe_id)
            for k, v in sub_data.items():
                setattr(obj, k, v)
            obj.save()
            complete += 1
    return complete == qs_count


def convert_user_ids_to_list(
    user_ids: Optional[List | str | int],
) -> List[Union[str, int]]:
    """Converts user IDs into a list for consistent processing.

    Args:
        user_ids (Optional[Union[List[int], str, int]]): User IDs as a list, single ID,
            or string. Returns an empty list if `None`.

    Returns:
        List[Union[str, int]]: A list of user IDs for further processing.
    """
    if user_ids is None:
        return []
    elif isinstance(user_ids, list):
        return user_ids
    elif isinstance(user_ids, int):
        return [user_ids]
    elif isinstance(user_ids, str):
        return [user_ids]


def clear_dangling_subscriptions() -> None:
    """Clears dangling subscriptions by syncing and canceling any that are not linked to active user subscriptions.

    This function iterates through customers with a `stripe_id`, retrieves their active subscriptions from Stripe,
    and cancels any subscriptions not found in the local `UserSubscription` database. It helps ensure data consistency
    by removing subscriptions that should no longer be active.

    Returns:
        None
    """
    qs = Customer.objects.filter(stripe_id__isnull=False)
    for customer_obj in qs:
        user = customer_obj.user

        customer_stripe_id = customer_obj.stripe_id
        logger.info(
            f"Sync {user}'s ({customer_stripe_id}) subscriptions and remove old ones"
        )
        # Retrieve active subscriptions from Stripe
        subscriptions = helpers.billing.get_customer_active_subscriptions(
            customer_stripe_id
        )
        for sub in subscriptions:
            existing_user_subs_qs = UserSubscription.objects.filter(
                stripe_id__iexact=f"{sub.id}".strip()
            )
            # Check if the subscription exists in database
            if not existing_user_subs_qs.exists():
                logging.info(f"Subscription {sub.id} is dangling: Canceling.")
                helpers.billing.cancel_subscription(
                    stripe_id=sub.id,
                    reason="Dangling Active Subscription",
                    cancel_at_period_end=True,
                )
    return


def sync_subscription_group_permissions() -> None:
    """Syncs permissions for groups associated with active subscriptions.

    This function iterates through all active `Subscription` objects and ensures that each
    group's permissions are updated to match the permissions assigned to the subscription.

    Returns:
        None
    """
    qs = Subscription.objects.filter(active=True)
    for obj in qs:
        subscription_permissions = obj.permissions.all()
        for group in obj.groups.all():
            # Update the group's permissions to match the subscription's permissions
            group.permissions.set(subscription_permissions)
    return
