from django.shortcuts import render
import helpers.number_utils
from visits.models import PageVisit

# Create your views here.

def landing_page_view(request):
    qs = PageVisit.objects.all()  # Get everything
    page_qs = PageVisit.objects.filter(path=request.path)
    PageVisit.objects.create(path=request.path)
    formatted_page_views = helpers.number_utils.format_number(page_qs.count())
    formatted_total_views = helpers.number_utils.format_number(qs.count())

    return render(request, 'landing/main.html',{'page_views':formatted_page_views, 'total_views':formatted_total_views})