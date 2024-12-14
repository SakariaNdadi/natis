from django.contrib import admin

from .models import Answer, LicenseType, Option, Question, Questionnaire

admin.site.register(LicenseType)
admin.site.register(Questionnaire)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(Answer)
