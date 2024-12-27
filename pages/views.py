import environ
from django.shortcuts import redirect, render

env = environ.Env()


def index(request):
    template_name = "pages/index.html"

    if request.user.is_authenticated:
        return redirect("exam:index")
    return render(request, template_name)


def about(request):
    template_name = "pages/about.html"
    return render(request, template_name)


def privacy(request):
    template_name = "pages/privacy.html"
    return render(request, template_name)


def license(request):
    template_name = "pages/license.html"
    return render(request, template_name)


def changelog(request):
    template_name = "pages/changelog.html"
    return render(request, template_name)


def contact(request):
    template_name = "pages/contact.html"
    CONTACT_FORM = env("CONTACT_FORM")
    context = {"source": CONTACT_FORM}
    return render(request, template_name, context)
