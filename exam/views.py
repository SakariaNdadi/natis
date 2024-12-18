from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import TakeExamForm
from .models import Answer, ExamSession, LicenseType, Questionnaire


@login_required
def index(request) -> HttpResponse:
    template_name = "index.html"
    exams = ExamSession.objects.filter(user=request.user, completed=True)
    exams_data = []

    for exam in exams:
        start_time = exam.start_time
        correct_count = exam.answers.filter(is_correct=True).count()
        total_questions = exam.questionnaire.questions.count()
        score_percentage = (
            (correct_count / total_questions) * 100 if total_questions > 0 else 0
        )

        exams_data.append(
            {
                "exam": exam,
                "questionnaire": exam.questionnaire,
                "correct_count": correct_count,
                "total_questions": total_questions,
                "score_percentage": score_percentage,
                "start_time": start_time,
            }
        )

    context = {"exams_data": exams_data}
    return render(request, template_name, context)


@login_required
def choose_license_type(request) -> HttpResponse:
    template_name = "exam/choose_license_type.html"
    context = {"license_types": LicenseType.objects.all()}
    return render(request, template_name, context)


@login_required
def choose_questionnaire(request, license_type_id) -> HttpResponse:
    template_name = "exam/choose_questionnaire.html"
    license_type = get_object_or_404(LicenseType, id=license_type_id)
    ongoing_sessions = ExamSession.objects.filter(
        user=request.user, completed=False
    ).values_list("questionnaire_id", flat=True)

    context = {
        "license_type": license_type,
        "questionnaires": license_type.questionnaires.all(),
        "ongoing_sessions": ongoing_sessions,
    }

    # Redirect to ongoing session if selected
    if request.method == "POST":
        questionnaire_id = request.POST.get("questionnaire_id")
        if int(questionnaire_id) in ongoing_sessions:
            return redirect("exam:take_exam", questionnaire_id=questionnaire_id)

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

    # Create a new or get the existing session
    exam_session, created = ExamSession.objects.get_or_create(
        user=request.user, questionnaire=questionnaire, completed=False
    )

    # Redirect if time is up
    if exam_session.is_time_up():
        exam_session.completed = True
        exam_session.save()
        return redirect("exam:review_exam", exam_session_id=exam_session.id)

    if request.method == "POST":
        form = TakeExamForm(questions, request.POST)
        if form.is_valid():
            form.save(session=exam_session)
            # exam_session.completed = True
            exam_session.save()
            return redirect("exam:review_exam", exam_session_id=exam_session.id)
    else:
        form = TakeExamForm(questions)

    time_left = max(
        (exam_session.start_time + timedelta(minutes=60)) - timezone.now(),
        timedelta(0),
    )

    context = {
        "questionnaire": questionnaire,
        "form": form,
        "time_left": time_left,
    }
    return render(request, template_name, context)


@login_required
def review_exam(request, exam_session_id) -> HttpResponse:
    template_name = "exam/review_exam.html"
    exam_session = get_object_or_404(ExamSession, id=exam_session_id)

    # Redirect to the result page if the exam is already completed
    if exam_session.completed:
        return redirect("exam:exam_result", exam_session_id=exam_session.id)

    if request.method == "POST":
        # Mark the session as completed when submitted
        exam_session.completed = True
        exam_session.end_time = timezone.now()
        exam_session.save()
        return redirect("exam:exam_result", exam_session_id=exam_session.id)

    context = {
        "questionnaire": exam_session.questionnaire,
        "answers": exam_session.answers.select_related("question", "response"),
    }
    return render(request, template_name, context)


@login_required
def exam_result(request, exam_session_id) -> HttpResponse:
    template_name = "exam/exam_result.html"
    exam_session = get_object_or_404(ExamSession, id=exam_session_id)
    user_answers = exam_session.answers.all()
    correct_count = user_answers.filter(is_correct=True).count()
    total_questions = exam_session.questionnaire.questions.count()

    context = {
        "answers": user_answers,
        "questionnaire": exam_session.questionnaire,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "score_percentage": (correct_count / total_questions) * 100,
    }
    return render(request, template_name, context)
