from django.urls import path
from . import views

urlpatterns = [
    # path("", home_page_view, name="home"),  # Root page
    path("<username>/", views.profile_view),
]
