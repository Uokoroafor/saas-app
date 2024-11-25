from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from visits.models import PageVisit
import pathlib
from typing import Any

LOGIN_URL = settings.LOGIN_URL

this_dir = pathlib.Path(__file__).resolve().parent


def old_home_page_view(
    request: HttpRequest, *args: Any, **kwargs: Any
) -> HttpResponse:
    """
    Renders and returns the content of the home.html file as an HTTP response.

    This function is now defunct.

    Args:
        request (HttpRequest): The HTTP request object.
        *args (Any): Additional positional arguments.
        **kwargs (Any): Additional keyword arguments.

    Returns:
        HttpResponse: The HTTP response containing the HTML content.
    """
    html_file_path = this_dir / "home.html"
    html_text = html_file_path.read_text()
    return HttpResponse(html_text)


def home_page_view(
    request: HttpRequest, *args: Any, **kwargs: Any
) -> HttpResponse:
    """
    Handles the request for the home page.

    If the user is authenticated, their first name is printed
    to the console. Delegates rendering to the `about_view` function.

    Args:
        request (HttpRequest): The HTTP request object.
        *args (Any): Additional positional arguments passed to the `about_view`.
        **kwargs (Any): Additional keyword arguments passed to the `about_view`.

    Returns:
        HttpResponse: The response returned by the `about_view` function.
    """
    if request.user.is_authenticated:
        print(request.user.first_name)
    return about_view(request, *args, **kwargs)


def about_view(
    request: HttpRequest, *args: Any, **kwargs: Any
) -> HttpResponse:
    """
    Handles requests for the "About" page, calculates and tracks page visit statistics,
    and renders the corresponding HTML template with the context.

    Args:
        request (HttpRequest): The HTTP request object.
        *args (Any): Additional positional arguments.
        **kwargs (Any): Additional keyword arguments.

    Returns:
        HttpResponse: The rendered HTML response for the "About" page.
    """
    qs = PageVisit.objects.all()  # Get everything
    page_qs = PageVisit.objects.filter(path=request.path)
    my_title = "My Page"
    try:
        percent = round(100 * page_qs.count() / qs.count(), 2)
    except ZeroDivisionError:
        percent = 0.0
    my_context = {
        "page_title": my_title,
        "page_visit_count": page_qs.count(),
        "total_visit_count": qs.count(),
        "percentage_split": percent,
    }
    html_template = "home.html"
    PageVisit.objects.create(path=request.path)
    return render(
        request=request, template_name=html_template, context=my_context
    )


VALID_CODE = "abc123"


def pw_protected_view(request, *args, **kwargs):
    """
    View for handling a password-protected page.

    If the user enters the correct password, they are allowed access
    to the protected page. Otherwise, they are redirected to an entry page
    where they can submit the password.

    Args:
        request (HttpRequest): The HTTP request object.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.

    Returns:
        HttpResponse: Rendered response for the appropriate page (entry or protected view).
    """
    is_allowed = request.session.get("protected_page_allowed") or 0
    if request.method == "POST":
        user_pw_sent = request.POST.get("code") or None
        if user_pw_sent == VALID_CODE:
            request.session["protected_page_allowed"] = 1
            is_allowed = 1

    if is_allowed:
        return render(
            request=request, template_name="protected/view.html", context={}
        )

    return render(
        request=request, template_name="protected/entry.html", context={}
    )


@login_required
def user_only_view(
    request: HttpRequest, *arg: Any, **kwargs: Any
) -> HttpResponse:
    """
    View accessible only to logged-in users.

    This view ensures that only authenticated users can access the
    protected content.

    Args:
        request (HttpRequest): The HTTP request object.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.

    Returns:
        HttpResponse: Rendered response for the user-only page.
    """
    return render(
        request=request, template_name="protected/user-only.html", context={}
    )


@staff_member_required(login_url=LOGIN_URL)
def staff_only_view(
    request: HttpRequest, *arg: Any, **kwargs: Any
) -> HttpResponse:
    """
    View accessible only to staff members.

    This view ensures that only staff members can access the
    protected content. Non-staff users are redirected to the login URL.

    Args:
        request (HttpRequest): The HTTP request object.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.

    Returns:
        HttpResponse: Rendered response for the staff-only page.
    """
    return render(
        request=request, template_name="protected/user-only.html", context={}
    )
