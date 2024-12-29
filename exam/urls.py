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
    path("read-rules/", views.rules, name="rules"),
    path("<int:questionnaire_id>/take/", views.take_exam, name="take_exam"),
    path("<int:exam_session_id>/review/", views.review_exam, name="review_exam"),
    path("<int:exam_session_id>/result/", views.exam_result, name="exam_result"),
    path(
        "<int:exam_session_id>/delete/",
        views.delete_exam_session,
        name="delete_exam_session",
    ),
    path(
        "mark-exam-complete/<int:exam_session_id>/",
        views.mark_exam_complete,
        name="mark_exam_complete",
    ),
]
