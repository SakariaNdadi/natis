from django.urls import path

from . import views

app_name = "exam"

urlpatterns = [
    path("", views.index, name="index"),
    path("license-types/", views.choose_license_type, name="choose_license_type"),
    path(
        "license-types/<int:license_type_id>/questionnaires/",
        views.choose_questionnaire,
        name="choose_questionnaire",
    ),
    path("read-rules/", views.read_rules, name="read_rules"),
    path("exam/<int:questionnaire_id>/take/", views.take_exam, name="take_exam"),
    path("exam/<int:exam_session_id>/review/", views.review_exam, name="review_exam"),
    path("exam/<int:exam_session_id>/result/", views.exam_result, name="exam_result"),
]
