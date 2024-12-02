from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
import helpers.number_utils
from visits.models import PageVisit
from dashboard.views import dashboard_view
from typing import Any

# Create your views here.


def landing_dashboard_page_view(
    request: HttpRequest, *args: Any, **kwargs: Any
) -> HttpResponse:
    """
    Handles requests for the new "Landing" page, calculates and tracks page visit statistics,
    and renders the corresponding HTML template with the context.

    Args:
        request (HttpRequest): The HTTP request object.
        *args (Any): Additional positional arguments.
        **kwargs (Any): Additional keyword arguments.

    Returns:
        HttpResponse: The rendered HTML response for the "Landing" page.
    """
    if request.user.is_authenticated:
        return dashboard_view(request)
    qs = PageVisit.objects.all()  # Get everything
    page_qs = PageVisit.objects.filter(path=request.path)
    PageVisit.objects.create(path=request.path)
    formatted_page_views = helpers.number_utils.format_number(page_qs.count())
    formatted_total_views = helpers.number_utils.format_number(qs.count())

    return render(
        request,
        "landing/main.html",
        {
            "page_views": formatted_page_views,
            "total_views": formatted_total_views,
        },
    )
