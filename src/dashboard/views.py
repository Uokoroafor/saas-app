from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


# Create your views here.
@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Displays the main dashboard for logged-in users.

    This view renders the dashboard page, which provides an overview of the user's
    activities or other relevant information. The page is accessible only to authenticated users.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the dashboard page (main.html) for the logged-in user.
    """
    return render(request, "dashboard/main.html", {})
