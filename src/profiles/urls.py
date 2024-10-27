from django.urls import path
from . import views

urlpatterns = [
    # path("", home_page_view, name="home"),  # Root page
    path("", views.profile_list_view),
    path("<username>/", views.profile_detail_view),
]
