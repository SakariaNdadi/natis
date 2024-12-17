from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import TakeExamForm
from .models import Answer, ExamSession, LicenseType, Questionnaire


def index(request) -> HttpResponse:
    template_name = "index.html"
    return render(request, template_name)


@login_required
def choose_license_type(request) -> HttpResponse:
    template_name = "exam/choose_license_type.html"
    context = {"license_types": LicenseType.objects.all()}
    return render(request, template_name, context)


@login_required
def choose_questionnaire(request, license_type_id) -> HttpResponse:
    template_name = "exam/choose_questionnaire.html"
    license_type = get_object_or_404(LicenseType, id=license_type_id)
    context = {
        "license_type": license_type,
        "questionnaires": license_type.questionnaires.all(),
    }
    return render(request, template_name, context)


@login_required
def read_rules(request) -> HttpResponse:
    template_name = "exam/read_rules.html"
    return render(request, template_name)


@login_required
def take_exam(request, questionnaire_id) -> HttpResponse:
    template_name = "exam/take_exam.html"
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    questions = questionnaire.questions.all().prefetch_related("options")

    exam_session, created = ExamSession.objects.get_or_create(
        user=request.user, questionnaire=questionnaire, completed=False
    )

    if exam_session.is_time_up():
        return redirect("exam:review_exam", questionnaire_id=questionnaire.id)

    if request.method == "POST":
        form = TakeExamForm(questions, request.POST)
        if form.is_valid():
            form.save(user=request.user, questionnaire=questionnaire)
            exam_session.completed = True
            exam_session.save()
            return redirect("exam:review_exam", questionnaire_id=questionnaire.id)
    else:
        form = TakeExamForm(questions)

    time_left = (exam_session.start_time + timedelta(minutes=60)) - timezone.now()

    context = {
        "questionnaire": questionnaire,
        "form": form,
        "time_left": time_left if time_left else timedelta(seconds=3600),
    }
    return render(request, template_name, context)


@login_required
def review_exam(request, questionnaire_id) -> HttpResponse:
    template_name = "exam/review_exam.html"
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    context = {
        "questionnaire": questionnaire,
        "answers": Answer.objects.filter(
            question__in=questionnaire.questions.all(), user=request.user
        ).select_related("question", "response"),
    }
    return render(request, template_name, context)


@login_required
def exam_result(request, questionnaire_id) -> HttpResponse:
    template_name = "exam/exam_result.html"
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    user_answers = Answer.objects.filter(
        question__in=questionnaire.question.all(), user=request.user
    )
    correct_count = user_answers.filter(is_correct=True).count()
    total_questions = questionnaire.question.count()
    context = {
        "questionnaire": questionnaire,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "score_percentage": (correct_count / total_questions) * 100,
    }
    return render(request, template_name, context)
