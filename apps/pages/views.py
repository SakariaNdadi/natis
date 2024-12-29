import environ
from django.shortcuts import redirect
from utils.views import render_page

env = environ.Env()


def index(request):
    if request.user.is_authenticated:
        return redirect("exam:index")
    return render_page(request, "pages/index.html")


def about(request):
    return render_page(request, "pages/about.html")


def privacy(request):
    return render_page(request, "pages/privacy.html")


def license(request):
    return render_page(request, "pages/license.html")


def changelog(request):
    return render_page(request, "pages/changelog.html")


def contact(request):
    context = {"source": env("CONTACT_FORM")}
    return render_page(request, "pages/contact.html", context)
