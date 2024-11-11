# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
import stripe
from decouple import config
from . import date_utils

DJANGO_DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="", cast=str)

if "sk_test" in STRIPE_SECRET_KEY and not DJANGO_DEBUG:
    raise ValueError("Invalid Stripe Key for Prod")
stripe.api_key = STRIPE_SECRET_KEY


def create_customer(name="", email="", raw=False, metadata={}):
    response = stripe.Customer.create(name=name, email=email, metadata=metadata)
    if raw:
        return response
    else:
        return response.id


def create_product(name="", raw=False, metadata={}):
    response = stripe.Product.create(name=name, metadata=metadata)
    if raw:
        return response
    else:
        return response.id


def create_price(
    currency="gbp",
    unit_amount="9999",
    recurring="month",
    product=None,
    raw=False,
    metadata={},
):
    if product is None:
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

def serialise_subscription_data(sub_response):
    status = sub_response.status

    current_period_start=date_utils.timestamp_as_datatime(sub_response.current_period_start)
    current_period_end=date_utils.timestamp_as_datatime(sub_response.current_period_end)

    return dict(current_period_start=current_period_start,
                         current_period_end=current_period_end,
                         status=status,)

def start_checkout_session(
    customer_id, success_url="", cancel_url="", price_stripe_id="", raw=False
):

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


def get_checkout_session(stripe_id, raw=False):
    response = stripe.checkout.Session.retrieve(id=stripe_id)
    if raw:
        return response
    return response.url


def get_subscription(stripe_id, raw=False):
    response = stripe.Subscription.retrieve(id=stripe_id)
    if raw:
        return response
    return serialise_subscription_data(sub_response=response)


def cancel_subscription(stripe_id, reason="Not stated", feedback="other", raw=False):
    response = stripe.Subscription.cancel(
        stripe_id, cancellation_details={"comment": reason, "feedback": feedback}
    )
    if raw:
        return response
    return response.id

def get_checkout_customer_plan(session_id):
    checkout_response = get_checkout_session(session_id, raw=True)
    customer_id = checkout_response.customer
    sub_stripe_id = checkout_response.subscription
    subscription_response = get_subscription(sub_stripe_id, raw=True)

    sub_plan = subscription_response.plan
    sub_plan_price_stripe_id = sub_plan.id
    # status = subscription_response.status

    # current_period_start=date_utils.timestamp_as_datatime(subscription_response.current_period_start)
    # current_period_end=date_utils.timestamp_as_datatime(subscription_response.current_period_end)

    serialised_sub_data = serialise_subscription_data(sub_response=subscription_response)

    response_data = dict(customer_id=customer_id,
                         sub_plan_price_stripe_id=sub_plan_price_stripe_id,
                         sub_stripe_id=sub_stripe_id,
                         **serialised_sub_data,
                         )

    return response_data
