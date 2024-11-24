from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def profile_list_view(request):
    context = {"object_list": User.objects.filter(is_active=True)}
    return render(request, "profiles/list.html", context)


# Create your views here.
@login_required
def profile_detail_view(request, username=None, *args, **kwargs):
    # profile_user_obj = User.objects.get(username=username)
    user = request.user
    print(
        user.has_perm("subscriptions.basic"),
        user.has_perm("subscriptions.pro"),
        user.has_perm("subscriptions.advanced"),
        user.has_perm("subscriptions.basic_ai"),
    )

    profile_user_obj = get_object_or_404(User, username=username)
    is_logged_in_user = profile_user_obj == user
    # logged_in_text = f"You are indeed {username}" if is_logged_in_user else f"You are not {username}!"
    context = {
        "object": profile_user_obj,
        "instance": profile_user_obj,
        "owner": is_logged_in_user,
    }
    return render(request, "profiles/detail.html", context)
