from django.http import HttpResponse
from django.shortcuts import render
from visits.models import PageVisit
import pathlib

this_dir = pathlib.Path(__file__).resolve().parent

def old_home_page_view(request, *args, **kwargs):
    html_file_path = this_dir / "home.html"
    html_text = html_file_path.read_text()
    return(HttpResponse(html_text))

def home_page_view(request, *args, **kwargs):
    qs = PageVisit.objects.all() # Get everything
    page_qs = PageVisit.objects.filter(path=request.path)
    my_title = "My Page"
    my_context = {
        "page_title": my_title,
        "page_visit_count": page_qs.count(),
        "total_visit_count": qs.count(),
    }
    html_template = "home.html"
    PageVisit.objects.create(path=request.path)
    return render(request=request,template_name=html_template, context = my_context)