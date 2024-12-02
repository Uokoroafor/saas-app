# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
import stripe
from decouple import config
from . import date_utils
from typing import Dict, Union, Optional, List
import datetime
import logging

logger = logging.getLogger("myproject")

DJANGO_DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="", cast=str)
STRIPE_TEST_KEY_OVERRIDE = config(
    "STRIPE_TEST_KEY_OVERRIDE", default=False, cast=bool
)

if (
    ("sk_test" in STRIPE_SECRET_KEY)
    and (not DJANGO_DEBUG)
    and (not STRIPE_TEST_KEY_OVERRIDE)
):
    logger.error("Invalid Stripe Key for Production Setting")
    raise ValueError("Invalid Stripe Key for Production Setting")
stripe.api_key = STRIPE_SECRET_KEY


def create_customer(
    name: str = "",
    email: str = "",
    raw: bool = False,
    metadata: Optional[Dict[str, str]] = None,
) -> Union[stripe.Customer, str]:
    """Creates a new customer in the Stripe system.

    Args:
        name (str, optional): The name of the customer. Defaults to an empty string.
        email (str, optional): The email address of the customer. Defaults to an empty string.
        raw (bool, optional): If `True`, returns the full Stripe customer object. If `False`, returns only the customer ID. Defaults to `False`.
        metadata (Dict[str, str], optional): Additional metadata to associate with the customer.
            Defaults to an empty dictionary.

    Returns:
        Union[stripe.Customer, str]: Returns a `stripe.Customer` object if `raw` is `True`,or the customer ID (`str`) if `raw` is `False`.
    """
    if not metadata:
        metadata = {}
    response = stripe.Customer.create(
        name=name, email=email, metadata=metadata
    )
    if raw:
        return response
    else:
        return response.id


def create_product(
    name: str = "",
    raw: bool = False,
    metadata: Optional[Dict[str, str]] = None,
) -> Union[stripe.Product, str]:
    """Creates a new product in the Stripe system.

    Args:
        name (str, optional): The name of the product. Defaults to an empty string.
        raw (bool, optional): If `True`, returns the full Stripe product object. If `False`, returns only
            the product ID. Defaults to `False`.
        metadata (Dict[str, str], optional): Additional metadata to associate with the product.
            Defaults to an empty dictionary.

    Returns:
        Union[stripe.Product, str]: Returns a `stripe.Product` object if `raw` is `True`,or the product ID (`str`)
            if `raw` is `False`.
    """
    if not metadata:
        metadata = {}
    response = stripe.Product.create(name=name, metadata=metadata)
    if raw:
        return response
    else:
        return response.id


def create_price(
    currency: str = "gbp",
    unit_amount: str = "9999",
    recurring: str = "month",
    product: Optional[str] = None,
    raw: bool = False,
    metadata: Optional[Dict[str, str]] = None,
) -> Union[stripe.Price, str]:
    """Creates a price object in Stripe for a given product.

    Args:
        currency (str, optional): The currency code (e.g., 'gbp', 'usd'). Defaults to "gbp".
        unit_amount (str, optional): The price amount in the smallest currency unit (e.g., cents).
            Defaults to "9999" (which represents £99.99 if using 'gbp').
        recurring (str, optional): The billing interval (e.g., 'month', 'year').
            Defaults to "month".
        product (Optional[str], optional): The ID of the product to associate with the price.
            Raises an error if not provided. Defaults to None.
        raw (bool, optional): Whether to return the full response object from Stripe.
            If False, returns only the price ID. Defaults to False.
        metadata (Optional[Dict[str, str]], optional): Additional metadata to associate with the price object.
            Defaults to None.

    Returns:
        Union[str, stripe.Price]: The ID of the created price if `raw` is False,
            otherwise the full `stripe.Price` object.

    Raises:
        ValueError: If `product` is not provided.
    """
    if product is None:
        logger.error("No Product included for created price")
        raise ValueError("No Product included for created price")
    response = stripe.Price.create(
        currency=currency,
        unit_amount=unit_amount,
        product=product,
        recurring={"interval": recurring},
        metadata=metadata,
    )
    if raw:
        return response
    else:
        return response.id


def serialise_subscription_data(
    sub_response: stripe.Subscription,
) -> Dict[str, Union[str, datetime.datetime, bool]]:
    """Serialises subscription data from the response object.

    Args:
        sub_response (stripe.Subscription): The subscription object.
            Expected to have the following attributes:
            - status (str): The current status of the subscription.
            - current_period_start (int): Unix timestamp for the start of the current period.
            - current_period_end (int): Unix timestamp for the end of the current period.
            - cancel_at_period_end (str): Indicator if the subscription is set to cancel.

    Returns:
        Dict[str, Union[str, datetime.datetime]]: A dictionary containing the serialised subscription data:
            - 'current_period_start' (datetime.datetime): Start of the current subscription period.
            - 'current_period_end' (datetime.datetime): End of the current subscription period.
            - 'status' (str): Current subscription status.
            - 'cancel_at_period_end' (bool): Indicates if the subscription will cancel at the end of the period.
    """
    status = sub_response.status

    current_period_start = date_utils.timestamp_as_datatime(
        sub_response.current_period_start
    )
    current_period_end = date_utils.timestamp_as_datatime(
        sub_response.current_period_end
    )
    cancel_at_period_end = sub_response.cancel_at_period_end

    return dict(
        current_period_start=current_period_start,
        current_period_end=current_period_end,
        status=status,
        cancel_at_period_end=cancel_at_period_end,
    )


def start_checkout_session(
    customer_id: str,
    success_url: str = "",
    cancel_url: str = "",
    price_stripe_id: str = "",
    raw: bool = False,
) -> Union[stripe.checkout.Session, str]:
    """Starts a Stripe checkout session for a subscription.

    Args:
        customer_id (str): The ID of the customer in Stripe.
        success_url (str, optional): The URL to redirect to upon successful checkout.
            Must end with "?session_id={CHECKOUT_SESSION_ID}". Defaults to an empty string.
        cancel_url (str, optional): The URL to redirect to if the checkout is canceled.
            Defaults to an empty string.
        price_stripe_id (str, optional): The Stripe price ID for the subscription.
            Defaults to an empty string.
        raw (bool, optional): If True, returns the full `stripe.checkout.Session` object.
            If False, returns the session URL. Defaults to False.

    Returns:
        Union[stripe.checkout.Session, str]: The full checkout session object if `raw` is True,
        otherwise the session URL as a string.
    """
    if not success_url.endswith("?session_id={CHECKOUT_SESSION_ID}"):
        success_url = f"{success_url}" + "?session_id={CHECKOUT_SESSION_ID}"

    response = stripe.checkout.Session.create(
        customer=customer_id,
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{"price": price_stripe_id, "quantity": 1}],
        mode="subscription",
    )

    if raw:
        return response
    return response.url


def get_checkout_session(
    stripe_id: str, raw: bool = False
) -> Union[stripe.checkout.Session, str]:
    """Retrieves a Stripe checkout session by its ID.

    Args:
        stripe_id (str): The unique ID of the Stripe checkout session to retrieve.
        raw (bool, optional): If True, returns the full `stripe.checkout.Session` object.
            If False, returns only the session URL. Defaults to False.

    Returns:
        Union[stripe.checkout.Session, str]: The full checkout session object if `raw` is True,
        otherwise the session URL as a string.
    """
    response = stripe.checkout.Session.retrieve(id=stripe_id)
    if raw:
        return response
    return response.url


def get_subscription(
    stripe_id: str, raw: bool = False
) -> Union[
    stripe.checkout.Session, Dict[str, Union[str, datetime.datetime, bool]]
]:
    """Retrieves a Stripe subscription by its ID and optionally serialises the data.

    Args:
        stripe_id (str): The unique ID of the Stripe subscription to retrieve.
        raw (bool, optional): If True, returns the full `stripe.Subscription` object.
            If False, returns a serialised dictionary of subscription data. Defaults to False.

    Returns:
        Union[stripe.Subscription, Dict[str, Union[str, datetime.datetime, bool]]]:
        The full subscription object if `raw` is True, or a dictionary containing:
            - 'current_period_start' (datetime.datetime): Start of the current subscription period.
            - 'current_period_end' (datetime.datetime): End of the current subscription period.
            - 'status' (str): Current subscription status.
            - 'cancel_at_period_end' (bool): Whether the subscription is set to cancel at the end of the period.
    """
    response = stripe.Subscription.retrieve(id=stripe_id)
    if raw:
        return response
    return serialise_subscription_data(sub_response=response)


def get_customer_active_subscriptions(
    customer_stripe_id: str,
) -> List[stripe.Subscription]:
    """Retrieves all active subscriptions for a given Stripe customer.

    Args:
        customer_stripe_id (str): The unique Stripe ID of the customer whose subscriptions are being retrieved.

    Returns:
        List[stripe.Subscription]: A list of active `stripe.Subscription` objects associated with the customer.
    """
    response = stripe.Subscription.list(
        customer=customer_stripe_id, status="active"
    )

    return response


def cancel_subscription(
    stripe_id: str,
    reason: str = "Not stated",
    feedback: str = "other",
    raw: bool = False,
    cancel_at_period_end: bool = False,
) -> Union[
    stripe.checkout.Session, Dict[str, Union[str, datetime.datetime, bool]]
]:
    """Cancels a Stripe subscription immediately or at the end of the billing period.

    Args:
        stripe_id (str): The unique ID of the Stripe subscription to cancel.
        reason (str, optional): A comment explaining the reason for cancellation. Defaults to "Not stated".
        feedback (str, optional): Feedback category related to the cancellation. Defaults to "other".
        raw (bool, optional): If True, returns the full `stripe.Subscription` object.
            If False, returns a serialised dictionary of subscription data. Defaults to False.
        cancel_at_period_end (bool, optional): If True, schedules the subscription to cancel
            at the end of the current billing period. If False, cancels immediately. Defaults to False.

    Returns:
        Union[stripe.Subscription, Dict[str, Union[str, datetime.datetime, bool]]]:
        The full subscription object if `raw` is True, or a dictionary containing:
            - 'current_period_start' (datetime.datetime): Start of the current subscription period.
            - 'current_period_end' (datetime.datetime): End of the current subscription period.
            - 'status' (str): Current subscription status.
            - 'cancel_at_period_end' (bool): Whether the subscription is set to cancel at the end of the period.
    """
    if cancel_at_period_end:
        response = stripe.Subscription.modify(
            stripe_id,
            cancel_at_period_end=cancel_at_period_end,
            cancellation_details={"comment": reason, "feedback": feedback},
        )

    else:
        response = stripe.Subscription.cancel(
            stripe_id,
            cancellation_details={"comment": reason, "feedback": feedback},
        )
    if raw:
        return response
    return serialise_subscription_data(sub_response=response)


def get_checkout_customer_plan(
    session_id: str,
) -> Dict[str, Union[str, datetime.datetime, bool]]:
    """Retrieves customer subscription details from a Stripe checkout session.

    Args:
        session_id (str): The ID of the Stripe checkout session.

    Returns:
        Dict[str, Union[str, datetime.datetime, bool]]: A dictionary containing subscription details, including:
            - 'customer_id' (str): The Stripe customer ID.
            - 'sub_plan_price_stripe_id' (str): The Stripe price ID associated with the subscription plan.
            - 'sub_stripe_id' (str): The Stripe subscription ID.
            - 'current_period_start' (datetime.datetime): Start of the current subscription period.
            - 'current_period_end' (datetime.datetime): End of the current subscription period.
            - 'status' (str): Current subscription status.
            - 'cancel_at_period_end' (bool): Indicates if the subscription will cancel at the end of the period.
    """
    checkout_response = get_checkout_session(session_id, raw=True)
    customer_id = checkout_response.customer
    sub_stripe_id = checkout_response.subscription
    subscription_response = get_subscription(sub_stripe_id, raw=True)

    sub_plan = subscription_response.plan
    sub_plan_price_stripe_id = sub_plan.id

    serialised_sub_data = serialise_subscription_data(
        sub_response=subscription_response
    )

    response_data = dict(
        customer_id=customer_id,
        sub_plan_price_stripe_id=sub_plan_price_stripe_id,
        sub_stripe_id=sub_stripe_id,
        **serialised_sub_data,
    )

    return response_data
