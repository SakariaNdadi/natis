from django.shortcuts import render


def index(request):
    template_name = "pages/index.html"
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
