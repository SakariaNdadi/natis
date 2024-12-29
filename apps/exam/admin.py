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

# Register basic models
admin.site.register(LicenseType)
admin.site.register(Answer)
admin.site.register(ExamSession)


# Questionnaire Admin
@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "license_type",
        "user",
        "question_count",  # Adding the number of questions
    )
    list_filter = ("license_type", "user")
    search_fields = ("title",)
    filter_horizontal = ("questions",)
    ordering = ("title",)
    list_per_page = 25

    def question_count(self, obj):
        """Returns the number of questions associated with the questionnaire"""
        return obj.questions.count()

    question_count.short_description = "Number of Questions"


# Option Admin
@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    search_fields = ["text"]


# QuestionOption Inline
class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    min_num = 3
    max_num = 3
    autocomplete_fields = ["option"]
    extra = 1  # Show one extra blank form in the inline


# Question Admin
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "section")
    inlines = [QuestionOptionInline]
    search_fields = (
        "question",
        "answer__text",
    )  # Search for both question text and answer option text
