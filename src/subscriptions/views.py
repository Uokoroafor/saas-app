from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from subscriptions.models import SubscriptionPrice, UserSubscription
import helpers.billing
import subscriptions.utils as subs_utils


# Create your views here.
def subscription_price_view(request, interval="month"):
    qs = SubscriptionPrice.objects.filter(featured=True)
    int_month = SubscriptionPrice.IntervalChoices.MONTHLY
    int_year = SubscriptionPrice.IntervalChoices.YEARLY
    url_path_name = "pricing_interval"
    month_url = reverse(url_path_name, kwargs={"interval": int_month})
    year_url = reverse(url_path_name, kwargs={"interval": int_year})
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
    request,
):
    user_sub_obj, created = UserSubscription.objects.get_or_create(
        user=request.user
    )
    _ = user_sub_obj.serialise()
    if request.method == "POST":
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

    return render(
        request,
        "subscriptions/user_detail_view.html",
        {"subscription": user_sub_obj},
    )


@login_required
def user_subscription_cancel_view(
    request,
):
    user_sub_obj, created = UserSubscription.objects.get_or_create(
        user=request.user
    )
    sub_data = user_sub_obj.serialise()
    if request.method == "POST":
        if user_sub_obj.stripe_id and user_sub_obj.is_active:
            sub_data = helpers.billing.cancel_subscription(
                user_sub_obj.stripe_id,
                reason="User chose to end",
                feedback="other",
                cancel_at_period_end=True,
                raw=False,
            )
            for k, v in sub_data.items():
                setattr(user_sub_obj, k, v)
            user_sub_obj.save()
            messages.success(
                request, "Your plan has been successfully cancelled."
            )
        return redirect(user_sub_obj.get_absolute_url())

    return render(
        request,
        "subscriptions/user_cancel_view.html",
        {"subscription": user_sub_obj},
    )
