from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from typing import Any, Optional

User = get_user_model()


@login_required
def profile_list_view(request: HttpRequest) -> HttpResponse:
    """Renders a list of active user profiles.

    This view retrieves all active users from the database and renders
    them in the 'profiles/list.html' template. Access to the view is
    restricted to authenticated users due to the `@login_required` decorator.

    Args:
        request (HttpRequest): The HTTP request object representing the
        incoming client request.

    Returns:
        HttpResponse: An HTTP response object containing the rendered
        template with the context data.
    """
    context = {"object_list": User.objects.filter(is_active=True)}
    return render(request, "profiles/list.html", context)


@login_required
def profile_detail_view(
    request: HttpRequest,
    username: Optional[str] = None,
    *args: Any,
    **kwargs: Any,
) -> HttpResponse:
    """Renders the detail view of a user profile.

    This view retrieves a user's profile based on the provided `username`.
    If the `username` is not found, a 404 error is raised.
    It also checks if the profile belongs to the currently logged-in user to determine ownership.

    Args:
        request (HttpRequest): The HTTP request object representing the incoming client request.
        username (Optional[str], optional): The username of the profile to display.
            Defaults to None.
        *args (Any): Additional positional arguments passed to the view.
        **kwargs (Any): Additional keyword arguments passed to the view.

    Returns:
        HttpResponse: An HTTP response object containing the rendered
        'profiles/detail.html' template with context data.
    """
    user = request.user

    profile_user_obj = get_object_or_404(User, username=username)
    is_logged_in_user = profile_user_obj == user

    context = {
        "object": profile_user_obj,
        "instance": profile_user_obj,
        "owner": is_logged_in_user,
    }
    return render(request, "profiles/detail.html", context)
