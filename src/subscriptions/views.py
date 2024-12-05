from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from subscriptions.models import SubscriptionPrice, UserSubscription
import helpers.billing
import subscriptions.utils as subs_utils


def subscription_price_view(
    request: HttpRequest, interval: str = "month"
) -> HttpResponse:
    """Displays subscription pricing based on the selected interval (monthly or yearly).

    This view fetches and renders featured subscription prices based on the specified billing interval.
    It also generates URLs for switching between monthly and yearly pricing views.

    Args:
        request (HttpRequest): The HTTP request object.
        interval (str): The billing interval, either "month" or "year". Defaults to "month".

    Returns:
        HttpResponse: The rendered pricing page with the appropriate subscription prices and URLs.
    """
    qs = SubscriptionPrice.objects.filter(featured=True)
    int_month = SubscriptionPrice.IntervalChoices.MONTHLY
    int_year = SubscriptionPrice.IntervalChoices.YEARLY
    url_path_name = "pricing_interval"

    # Generate URLs for the monthly and yearly pricing views
    month_url = reverse(url_path_name, kwargs={"interval": int_month})
    year_url = reverse(url_path_name, kwargs={"interval": int_year})

    # Filter subscription prices based on the interval
    if interval == "year":
        object_list = qs.filter(interval=int_year)
        active = int_year
    else:
        object_list = qs.filter(interval=int_month)
        active = int_month

    return render(
        request,
        "subscriptions/pricing.html",
        {
            "object_list": object_list,
            "month_url": month_url,
            "year_url": year_url,
            "active": active,
        },
    )


@login_required
def user_subscription_view(
    request: HttpRequest,
) -> HttpResponse:
    """Handles viewing and refreshing the current user's subscription details.

    This view retrieves the user's subscription object or creates one if it doesn't exist.
    It also handles POST requests to refresh subscription details by syncing data from Stripe.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse:
            - If the request is GET: Renders the user's subscription detail page.
            - If the request is POST: Redirects to the subscription detail page after attempting
                to refresh subscription data.
    """
    # Retrieve or create the UserSubscription object for the logged-in user
    user_sub_obj, created = UserSubscription.objects.get_or_create(
        user=request.user
    )

    # Serialise the subscription object (for potential future use)
    _ = user_sub_obj.serialise()
    if request.method == "POST":
        # Attempt to refresh the user's subscription details
        finished = subs_utils.refresh_active_users_subscriptions(
            user_ids=request.user.id, active_only=False
        )

        if finished:
            messages.success(request, "Your plan details have been refreshed!")
        else:
            messages.error(
                request,
                "Your plan details have not been refreshed. Please contact us.",
            )
        return redirect(user_sub_obj.get_absolute_url())
    # Render the subscription detail view for GET requests
    return render(
        request,
        "subscriptions/user_detail_view.html",
        {"subscription": user_sub_obj},
    )


@login_required
def user_subscription_cancel_view(
    request: HttpRequest,
) -> HttpResponse:
    """Handles the cancellation of the logged-in user's subscription.

    This view allows users to cancel their active subscription by sending a cancellation
    request to Stripe. The cancellation can be confirmed and processed via a POST request.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse:
            - If the request is GET: Renders the subscription cancellation confirmation page.
            - If the request is POST: Cancels the subscription and redirects to the subscription detail page.
    """
    # Retrieve or create the UserSubscription object for the logged-in user
    user_sub_obj, created = UserSubscription.objects.get_or_create(
        user=request.user
    )

    # Serialise the subscription data (for potential further use)
    sub_data = user_sub_obj.serialise()
    if request.method == "POST":
        # Proceed only if the subscription has an active Stripe ID and is active
        if user_sub_obj.stripe_id and user_sub_obj.is_active:
            sub_data = helpers.billing.cancel_subscription(
                user_sub_obj.stripe_id,
                reason="User chose to end",
                feedback="other",
                cancel_at_period_end=True,
                raw=False,
            )
            # Update local subscription object with the latest data from Stripe
            for k, v in sub_data.items():
                setattr(user_sub_obj, k, v)
            user_sub_obj.save()
            messages.success(
                request, "Your plan has been successfully cancelled."
            )
        return redirect(user_sub_obj.get_absolute_url())

    # Render the subscription cancellation confirmation page for GET requests
    return render(
        request,
        "subscriptions/user_cancel_view.html",
        {"subscription": user_sub_obj},
    )
