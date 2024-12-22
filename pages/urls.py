from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("privacy-policy/", views.privacy, name="privacy"),
    path("licensing/", views.license, name="licensing"),
    path("changelog/", views.changelog, name="changelog"),
]
