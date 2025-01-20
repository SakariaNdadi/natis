from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
    path("account/", include("apps.accounts.urls")),
    path("exam/", include("apps.exam.urls", namespace="exam")),
    path("", include("apps.pages.urls", namespace="pages")),
]

if not settings.DEBUG:
    urlpatterns.append(path("not/admin/", admin.site.urls))
else:
    urlpatterns.append(path("admin/", admin.site.urls))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
