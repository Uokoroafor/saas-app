from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login


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

# Create your views here.
def login_view(request):
    if request.method == 'POST':
        username = request.POST["username"] or None
        password = request.POST["password"] or None
        if all([username, password]):
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                print('Login Here Fam!')
                return redirect("/")
    return render(request, "auth/login.html", {})

# def register_view(request):
#     return render(request, "auth/login.html", {})