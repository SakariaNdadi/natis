from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("account/", include("accounts.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
    path("exam/", include("exam.urls", namespace="exam")),
    path("", include("pages.urls", namespace="pages")),
]

if not settings.DEBUG:
    urlpatterns.append(path("not/admin", admin.site.urls))
else:
    urlpatterns.append(path("admin/", admin.site.urls))
