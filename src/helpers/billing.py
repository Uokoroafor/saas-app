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
    
def create_product(name="",raw=False, metadata={}):
    response = stripe.Product.create(name=name,metadata=metadata)
    if raw:
        return response
    else:
        return response.id

def create_price(currency="gbp",unit_amount="9999", recurring="month", product=None,raw=False, metadata={}):
    if product is None:
        raise ValueError("No Product included for created price")
    response = stripe.Price.create(currency=currency, unit_amount=unit_amount, product=product, recurring={"interval": recurring},metadata=metadata)
    if raw:
        return response
    else:
        return response.id