# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
import stripe
from decouple import config

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
