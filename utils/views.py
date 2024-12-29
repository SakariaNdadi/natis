from django.http import HttpResponse
from django.shortcuts import render


def render_page(request, template_name, context=None) -> HttpResponse:
    """
    Renders a template with the provided context.

    Parameters:
        request (HttpRequest): The request object.
        template_name (str): The name of the template to render.
        context (dict, optional): The context data to pass to the template. Defaults to an empty dictionary.

    Returns:
        HttpResponse: The rendered response with the given template and context.
    """
    context = context or {}
    return render(request, template_name, context)
