from allauth.account.views import LoginView, LogoutView


class CustomLogin(LoginView):
    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["account/partial/login.html"]
        return ["account/login.html"]


class CustomLogout(LogoutView):
    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["account/partial/logout.html"]
        return ["account/logout.html"]
