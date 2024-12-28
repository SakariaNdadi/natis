import random
from collections import defaultdict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import TakeExamForm
from .models import Answer, ExamSession, LicenseType, Question, Questionnaire


@login_required
def index(request) -> HttpResponse:
    template_name = "exam/index.html"
    exams = ExamSession.objects.filter(user=request.user, completed=True)
    exams_data = []
    questionnaire_scores = defaultdict(list)

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

        questionnaire_scores[exam.questionnaire.title].append(score_percentage)

    avg_scores = {
        questionnaire: sum(scores) / len(scores)
        for questionnaire, scores in questionnaire_scores.items()
    }

    context = {
        "exams_data": exams_data,
        "avg_scores_labels": [label.capitalize() for label in avg_scores.keys()],
        "avg_scores_data": list(avg_scores.values()),
    }
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
    user_questionnaires = license_type.questionnaires.filter(user=request.user)

    context = {
        "license_type": license_type,
        "questionnaires": license_type.questionnaires.filter(user__isnull=True),
        "user_questionnaires": user_questionnaires,
        "ongoing_sessions": ongoing_sessions,
    }

    if request.method == "POST":
        # Handle redirect to ongoing session
        questionnaire_id = request.POST.get("questionnaire_id")
        if questionnaire_id and int(questionnaire_id) in ongoing_sessions:
            return redirect("exam:take_exam", questionnaire_id=questionnaire_id)

        # Handle random questionnaire generation
        if "generate_random" in request.POST:
            title = request.POST.get("title", "").strip()
            if not title:
                messages.error(request, "Please provide a title for the questionnaire.")
            else:
                # Fetch all questions related to the license type
                questions = Question.objects.filter(
                    questionnaires__license_type=license_type
                )
                if not questions.exists():
                    messages.error(
                        request, "No questions available for this license type."
                    )
                    return redirect(
                        "exam:choose_questionnaire", license_type_id=license_type.id
                    )

                # Pick a random question
                random_question = random.choice(questions)

                # Create the questionnaire and associate it with the user
                questionnaire = Questionnaire.objects.create(
                    title=title.lower(), license_type=license_type, user=request.user
                )
                questionnaire.questions.add(random_question)
                questionnaire.save()

                messages.success(
                    request,
                    f"Random questionnaire '{questionnaire.title}' has been generated successfully!",
                )
                return redirect(
                    "exam:choose_questionnaire", license_type_id=license_type.id
                )

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
        exam_session.completed = True
        exam_session.save()
        return redirect("exam:review_exam", exam_session_id=exam_session.id)

    if request.method == "POST":
        form = TakeExamForm(questions, request.POST)
        if form.is_valid():
            form.save(session=exam_session)
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
