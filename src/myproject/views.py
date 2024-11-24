from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from visits.models import PageVisit
import pathlib

LOGIN_URL = settings.LOGIN_URL

this_dir = pathlib.Path(__file__).resolve().parent


def old_home_page_view(request, *args, **kwargs):
    html_file_path = this_dir / "home.html"
    html_text = html_file_path.read_text()
    return HttpResponse(html_text)


def home_page_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        print(request.user.first_name)
    return about_view(request, *args, **kwargs)


def about_view(request, *args, **kwargs):
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
    return render(request=request, template_name=html_template, context=my_context)


VALID_CODE = "abc123"


def pw_protected_view(request, *args, **kwargs):
    is_allowed = request.session.get("protected_page_allowed") or 0
    if request.method == "POST":
        user_pw_sent = request.POST.get("code") or None
        if user_pw_sent == VALID_CODE:
            request.session["protected_page_allowed"] = 1
            is_allowed = 1

    if is_allowed:
        return render(request=request, template_name="protected/view.html", context={})

    return render(request=request, template_name="protected/entry.html", context={})


@login_required
def user_only_view(request, *args, **kwargs):
    return render(request=request, template_name="protected/user-only.html", context={})


@staff_member_required(login_url=LOGIN_URL)
def staff_only_view(request, *args, **kwargs):
    return render(request=request, template_name="protected/user-only.html", context={})
