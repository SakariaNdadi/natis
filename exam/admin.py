from django.contrib import admin

from .models import (
    Answer,
    ExamSession,
    LicenseType,
    Option,
    Question,
    Questionnaire,
    QuestionOption,
)

admin.site.register(LicenseType)
# admin.site.register(Questionnaire)
# admin.site.register(Question)
# admin.site.register(Option)
admin.site.register(Answer)
admin.site.register(ExamSession)


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "license_type",
        "user",
    )
    list_filter = ("license_type", "user")
    search_fields = ("title",)
    filter_horizontal = ("questions",)
    ordering = ("title",)
    list_per_page = 25


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    search_fields = ["text"]


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    # extra = 1
    max_num = 3
    autocomplete_fields = ["option"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "section")
    inlines = [QuestionOptionInline]
    search_fields = ("answer",)
