from typing import Any, Dict, Optional, Tuple, Union
from django.shortcuts import render, redirect
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from subscriptions.models import (
    SubscriptionPrice,
    Subscription,
    UserSubscription,
)
import helpers.billing
import warnings
import logging

logger = logging.getLogger("myproject")

BASE_URL = settings.BASE_URL
User = get_user_model()


# Create your views here.
def product_price_redirect_view(
    request: HttpRequest,
    price_id: Optional[str] = None,
    *args: Any,
    **kwargs: Any,
) -> Union[HttpResponseRedirect, HttpResponsePermanentRedirect]:
    """
    Store the subscription price ID in the session and redirect to the Stripe checkout start page.

    Args:
        request (HttpRequest): The HTTP request object containing session data.
        price_id (Optional[str]): The price ID for the subscription, if provided. Defaults to None.
        *args (Any): Additional positional arguments (not used in this view).
        **kwargs (Any): Additional keyword arguments (not used in this view).

    Returns:
        Union[HttpResponseRedirect, HttpResponsePermanentRedirect]: A redirection response
        to the "stripe-checkout-start" URL.
    """
    request.session["checkout_subscription_price_id"] = price_id
    return redirect("stripe-checkout-start")


@login_required
def checkout_redirect_view(
    request: HttpRequest,
) -> Union[HttpResponseRedirect, HttpResponsePermanentRedirect]:
    """
    Redirect the user to the Stripe checkout session if a valid subscription price is found in the session.

    Retrieves the subscription price ID from the session, attempts to fetch the corresponding
    `SubscriptionPrice` object, and starts a Stripe checkout session if valid. Redirects the user
    to the pricing page if no valid price ID is found.

    Args:
        request (HttpRequest): The HTTP request object containing session and user data.

    Returns:
        Union[HttpResponseRedirect, HttpResponsePermanentRedirect]: A redirect response to the
        Stripe checkout session URL or the pricing page.
    """
    checkout_subscription_price_id = request.session.get(
        "checkout_subscription_price_id"
    )

    try:
        obj = SubscriptionPrice.objects.get(id=checkout_subscription_price_id)
    except Exception as e:
        msg = f"Error fetching Subscription's Price: {e}"
        warnings.warn(msg, RuntimeWarning)
        logger.warning(msg)
        obj = None
    if checkout_subscription_price_id is None or obj is None:
        return redirect("pricing")
    customer_stripe_id = request.user.customer.stripe_id

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


def checkout_finalise_view(
    request: HttpRequest,
) -> Union[HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect]:
    """
    Finalises the checkout process by associating a subscription with the user and managing
    subscription data updates.

    Args:
        request (HttpRequest): The HTTP request object containing session and GET data.

    Returns:
        Union[HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect]:
        - A redirect to the user's subscription URL upon successful processing.
        - An error response if any issues arise during processing.
    """
    session_id = request.GET.get("session_id")
    checkout_data = helpers.billing.get_checkout_customer_plan(session_id)

    customer_id = checkout_data.pop("customer_id")
    sub_plan_price_stripe_id = checkout_data.pop("sub_plan_price_stripe_id")
    sub_stripe_id = checkout_data.pop("sub_stripe_id")

    subscription_data = checkout_data

    # Retrieve the subscription object
    sub_obj = get_subscription(sub_plan_price_stripe_id)

    # Retrieve or create the UserSubscription object
    user_obj = get_user_subscription(customer_id)

    context: Dict[str, str] = {}

    updated_sub_options = {
        "subscription": sub_obj,
        "stripe_id": sub_stripe_id,
        "user_cancelled": False,
        **subscription_data,
    }
    _user_sub_exists, _user_sub_obj = get_or_create_user_subscription_object(
        user_obj, updated_sub_options
    )

    # Log Subscription, User and User Subscription
    logger.info(
        "Subscription",
        sub_obj,
        "\nUser",
        user_obj,
        "\nUser Subscription",
        _user_sub_obj,
    )
    # Error handling for missing objects
    if None in [sub_obj, user_obj, _user_sub_obj]:
        logger.error(
            f"There was an error: \nsub_obj_error:{sub_obj is None},\nuser_obj_error:{user_obj is None},\n_user_sub_obj_error:{_user_sub_obj is None}"
        )
        return HttpResponseBadRequest(
            "There was an error with your requested purchase. Please contact us!"
        )

    if _user_sub_exists:
        # cancel existing subscription if it exists
        old_stripe_id = _user_sub_obj.stripe_id

        cancel_existing_sub_if_any(old_stripe_id, sub_stripe_id)

        # Update the UserSubscription object in the database
        for key, value in updated_sub_options.items():
            setattr(_user_sub_obj, key, value)
        _user_sub_obj.save()
        messages.success(request, "Success. Great to have you onboard!")
        return redirect(_user_sub_obj.get_absolute_url())
    return render(request, "checkout/success.html", context=context)


def cancel_existing_sub_if_any(
    old_stripe_id: Optional[str], stripe_id: Optional[str]
) -> None:
    """
    Cancels the old subscription if a new one is created with a different Stripe ID.

    Args:
        old_stripe_id (Optional[str]): The Stripe ID of the existing subscription to cancel.
        stripe_id (Optional[str]): The Stripe ID of the new subscription to compare with the old one.

    Returns:
        None: This function does not return anything.
    """
    same_stripe_id = stripe_id == old_stripe_id
    if old_stripe_id is not None and not same_stripe_id:
        try:
            helpers.billing.cancel_subscription(
                old_stripe_id,
                reason="Created new membership. Auto cancelling old membership",
            )
        except Exception as e:
            msg = (
                f"Error cancelling subscription with ID '{old_stripe_id}': {e}"
            )
            warnings.warn(msg, RuntimeWarning)
            logger.warning(msg)


def get_user_subscription(customer_id: str) -> Optional[AbstractUser]:
    """
    Retrieves the `AbstractUser` object associated with the given Stripe customer ID.

    Args:
        customer_id (str): The Stripe customer ID used to look up the user.

    Returns:
        Optional[AbstractUser]: The user object associated with the customer ID,
        or `None` if an error occurs or the user is not found.
    """
    try:
        user_obj = User.objects.get(
            customer__stripe_id=customer_id
        )  # Basically a reverse lookup to get the subscription from the subscription price object
    except Exception as e:
        msg = f"Error fetching User Object: {e}"
        warnings.warn(msg, RuntimeWarning)
        logger.warning(msg)
        user_obj = None
    return user_obj


def get_subscription(sub_plan_price_stripe_id: str) -> Optional[Subscription]:
    """
    Retrieves the `Subscription` object associated with the given Stripe price ID.

    Args:
        sub_plan_price_stripe_id (str): The Stripe price ID used to look up the subscription.

    Returns:
        Optional[Subscription]: The subscription object associated with the price ID,
        or `None` if an error occurs or the subscription is not found.
    """
    try:
        sub_obj = Subscription.objects.get(
            subscriptionprice__stripe_id=sub_plan_price_stripe_id
        )  # Basically a reverse lookup to get the subscription from the subscription price object
    except Exception as e:
        msg = f"Error fetching Subscription Object: {e}"
        warnings.warn(msg, RuntimeWarning)
        logger.warning(msg)
        sub_obj = None
    return sub_obj


def get_or_create_user_subscription_object(
    user_obj: AbstractUser,
    updated_sub_options: Dict[str, Union[str, int, bool]],
) -> Tuple[bool, Optional[UserSubscription]]:
    """
    Retrieves or creates a `UserSubscription` object for a given user.

    Args:
        user_obj (AbstractUser): The user for whom the subscription object is being retrieved or created.
        updated_sub_options (Dict[str, Union[str, int, bool]]):
            A dictionary containing additional options or data to update the `UserSubscription`.

    Returns:
        Tuple[bool, Optional['UserSubscription']]:
            A tuple containing a boolean indicating if the subscription existed (`True` if it exists)
            and the `UserSubscription` object itself (or `None` if an error occurred).
    """
    _user_sub_exists = False
    try:
        _user_sub_obj = UserSubscription.objects.get(user=user_obj)
        _user_sub_exists = True
    except UserSubscription.DoesNotExist:
        _user_sub_obj = UserSubscription.objects.create(
            user=user_obj, **updated_sub_options
        )
    except Exception as e:
        msg = f"Error fetching User's subscription: {e}"
        warnings.warn(msg, RuntimeWarning)
        logger.warning(msg)
        _user_sub_obj = None
    return _user_sub_exists, _user_sub_obj
