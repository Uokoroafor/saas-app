from django.http import HttpResponse
from django.shortcuts import render
from visits.models import PageVisit
import pathlib

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
