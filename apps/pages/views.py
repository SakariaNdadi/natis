import environ
from django.http import HttpResponse
from django.shortcuts import redirect, render

from apps.notifications.models import Announcement

env = environ.Env()


def index(request) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("exam:index")

    context = {"announcements": Announcement.objects.filter(is_visible=True)}
    return render(request, "pages/index.html", context)


def about(request) -> HttpResponse:
    return render(request, "pages/about.html")


def privacy(request) -> HttpResponse:
    return render(request, "pages/privacy.html")


def license(request) -> HttpResponse:
    return render(request, "pages/license.html")


def changelog(request) -> HttpResponse:
    return render(request, "pages/changelog.html")


def contact(request) -> HttpResponse:
    context = {"source": env("CONTACT_FORM")}
    return render(request, "pages/contact.html", context)
