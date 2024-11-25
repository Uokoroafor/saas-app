from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.http import HttpResponse, HttpRequest
import warnings

# def my_view(request):
#     username = request.POST["username"]
#     password = request.POST["password"]
#     user = authenticate(request, username=username, password=password)
#     if user is not None:
#         login(request, user)
#         # Redirect to a success page.
#         ...
#     else:
#         # Return an 'invalid login' error message.
#         ...

User = get_user_model()


# Create your views here.
def login_view(request: HttpRequest) -> HttpResponse:
    """
    Handles user login requests.

    If the request method is POST, it attempts to authenticate the user using
    the provided username and password. On successful authentication, the user
    is logged in and redirected to the homepage. Otherwise, the login form is re-rendered.

    Args:
        request (HttpRequest): The HTTP request object containing method,
        POST data, and session info.

    Returns:
        HttpResponse: The HTTP response rendering the login page or redirecting
        to the homepage upon successful login.
    """
    if request.method == "POST":
        # Retrieve username and password from POST data
        username = request.POST["username"] or None
        password = request.POST["password"] or None

        # Proceed if both username and password are provided
        if all([username, password]):
            user = authenticate(request, username=username, password=password)
            # Login authenticated user and redirect to home page
            if user is not None:
                login(request, user)
                return redirect("/")
    # Render the default login form for unsuccessful POST or other requests
    return render(request, "auth/login.html", {})


def register_view(request: HttpRequest) -> HttpResponse:
    """
    Handles user registration requests.

    If the request method is POST, it attempts to create a new user account using
    the provided username, email, and password. If the account creation is successful,
    the user is added to the database. On failure, the registration form is re-rendered.

    Args:
        request (HttpRequest): The HTTP request object containing method, POST data, and session info.

    Returns:
        HttpResponse: The HTTP response rendering the registration page.
    """
    if request.method == "POST":
        # Retrieve registration details from POST data
        username = request.POST["username"] or None
        email = request.POST["email"] or None
        password = request.POST["password"] or None

        if all([username, email, password]):
            # Create new user
            try:
                User.objects.create_user(
                    username=username, email=email, password=password
                )

            except Exception as e:
                warnings.warn(f"Error registering user {username}: {e}", RuntimeWarning)
    # Render the registration form for after failed POST attempts or other requests
    return render(request, "auth/register.html", {})
