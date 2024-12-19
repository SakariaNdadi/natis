from django.urls import path
from . import views

urlpatterns = [
    path("accounts/login/", views.CustomLogin.as_view(), name="account_login"),
    path("accounts/logout/", views.CustomLogout.as_view(), name="account_logout"),
]
