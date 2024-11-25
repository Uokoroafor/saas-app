from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from subscriptions.models import (
    SubscriptionPrice,
    Subscription,
    UserSubscription,
)
import helpers.billing
import warnings

BASE_URL = settings.BASE_URL
User = get_user_model()


# Create your views here.
def product_price_redirect_view(request, price_id=None, *args, **kwargs):
    request.session["checkout_subscription_price_id"] = price_id
    return redirect("stripe-checkout-start")


@login_required
def checkout_redirect_view(request):
    checkout_subscription_price_id = request.session.get(
        "checkout_subscription_price_id"
    )
    # print("checkout_subscription_price_id",checkout_subscription_price_id)
    try:
        obj = SubscriptionPrice.objects.get(id=checkout_subscription_price_id)
    except Exception as e:
        warnings.warn(
            f"Error fetching Subscription's Price: {e}", RuntimeWarning
        )
        obj = None
    if checkout_subscription_price_id is None or obj is None:
        return redirect("pricing")
    customer_stripe_id = request.user.customer.stripe_id
    # print(customer_stripe_id)
    success_url_end = reverse("stripe-checkout-end")
    pricing_url_path = reverse("pricing")
    success_url = f"{BASE_URL}{success_url_end}"
    cancel_url = f"{BASE_URL}{pricing_url_path}"
    price_stripe_id = obj.stripe_id
    url = helpers.billing.start_checkout_session(
        customer_id=customer_stripe_id,
        success_url=success_url,
        cancel_url=cancel_url,
        price_stripe_id=price_stripe_id,
        raw=False,
    )
    return redirect(url)


def checkout_finalise_view(request):
    session_id = request.GET.get("session_id")
    checkout_data = helpers.billing.get_checkout_customer_plan(session_id)

    customer_id = checkout_data.pop("customer_id")
    sub_plan_price_stripe_id = checkout_data.pop("sub_plan_price_stripe_id")
    sub_stripe_id = checkout_data.pop("sub_stripe_id")
    # current_period_start = checkout_data.get('current_period_start')
    # current_period_end = checkout_data.get('current_period_end')

    subscription_data = checkout_data
    # print(checkout_data)

    # Get Subscription
    try:
        sub_obj = Subscription.objects.get(
            subscriptionprice__stripe_id=sub_plan_price_stripe_id
        )  # Basically a reverse lookup to get the subscription from the subscription price object
    except Exception as e:
        warnings.warn(
            f"Error fetching Subscription Object: {e}", RuntimeWarning
        )
        sub_obj = None

    # Get User
    try:
        user_obj = User.objects.get(
            customer__stripe_id=customer_id
        )  # Basically a reverse lookup to get the subscription from the subscription price object
    except Exception as e:
        warnings.warn(f"Error fetching User Object: {e}", RuntimeWarning)
        user_obj = None
    context = {}

    _user_sub_exists = False
    updated_sub_options = {
        "subscription": sub_obj,
        "stripe_id": sub_stripe_id,
        "user_cancelled": False,
        **subscription_data,
    }
    try:
        _user_sub_obj = UserSubscription.objects.get(user=user_obj)
        _user_sub_exists = True
    except UserSubscription.DoesNotExist:
        _user_sub_obj = UserSubscription.objects.create(
            user=user_obj, **updated_sub_options
        )
    except Exception as e:
        warnings.warn(
            f"Error fetching User's subscription: {e}", RuntimeWarning
        )
        _user_sub_obj = None

    print(
        "Subscription",
        sub_obj,
        "\nUser",
        user_obj,
        "\nUser Subscription",
        _user_sub_obj,
    )
    if None in [sub_obj, user_obj, _user_sub_obj]:
        return HttpResponseBadRequest(
            "There was an error with your requested purchase. Please contact us!"
        )

    if _user_sub_exists:
        # cancel old sub
        old_stripe_id = _user_sub_obj.stripe_id
        same_stripe_id = sub_stripe_id == old_stripe_id
        if old_stripe_id is not None and not same_stripe_id:
            try:
                helpers.billing.cancel_subscription(
                    old_stripe_id,
                    reason="Created new membership. Auto cancelling old membership",
                )
            except Exception as e:
                warnings.warn(
                    f"Error fetching User Object: {e}", RuntimeWarning
                )

        # This replaces the subscription in the database
        for key, value in updated_sub_options.items():
            setattr(_user_sub_obj, key, value)
        _user_sub_obj.save()
        messages.success(request, "Success. Great to have you onboard!")
        return redirect(_user_sub_obj.get_absolute_url())
    return render(request, "checkout/success.html", context=context)
