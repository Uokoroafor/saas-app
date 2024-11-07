from django.shortcuts import render
from django.urls import reverse
from subscriptions.models import SubscriptionPrice
# Create your views here.
def subscription_price_view(request, interval="month"):
    qs= SubscriptionPrice.objects.filter(featured=True)
    int_month = SubscriptionPrice.IntervalChoices.MONTHLY
    int_year = SubscriptionPrice.IntervalChoices.YEARLY
    url_path_name = "pricing_interval"
    month_url = reverse(url_path_name, kwargs={'interval': int_month})
    year_url = reverse(url_path_name, kwargs={'interval': int_year})
    if interval=="year":
        object_list = qs.filter(interval=int_year)
        active=int_year
    else:
        object_list = qs.filter(interval=int_month)
        active=int_month
    
    return render(request, "subscriptions/pricing.html", {"object_list":object_list, "month_url": month_url, "year_url":year_url, "active":active})