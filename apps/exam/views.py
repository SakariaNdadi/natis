import random
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, F, ExpressionWrapper, FloatField
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from utils.views import render_page

from .forms import TakeExamForm
from .models import ExamSession, LicenseType, Question, Questionnaire


@login_required
def index(request):
    # Fetch exams with necessary related data using select_related and prefetch_related
    exams = (
        ExamSession.objects.filter(user=request.user, completed=True)
        .select_related("questionnaire")  # For faster access to questionnaire
        .prefetch_related(
            "answers", "questionnaire__questions"
        )  # For answers and questions
        .annotate(
            correct_count=Count("answers", filter=F("answers__is_correct")),
            total_questions=Count("questionnaire__questions"),
        )
    )

    # Initialize data structures
    exams_data = []
    questionnaire_scores = defaultdict(list)

    # Process each exam in a single loop
    for exam in exams:
        correct_count = exam.correct_count
        total_questions = exam.total_questions
        score_percentage = (
            (correct_count / total_questions) * 100 if total_questions > 0 else 0
        )

        # Append the data for each exam
        exams_data.append(
            {
                "exam": exam,
                "questionnaire": exam.questionnaire,
                "correct_count": correct_count,
                "total_questions": total_questions,
                "score_percentage": score_percentage,
                "start_time": exam.start_time,
            }
        )

        questionnaire_scores[exam.questionnaire.title].append(score_percentage)

    # Calculate average scores for each questionnaire
    avg_scores = {
        questionnaire: sum(scores) / len(scores)
        for questionnaire, scores in questionnaire_scores.items()
    }

    # Prepare the context for rendering the page
    context = {
        "exams_data": exams_data,
        "avg_scores_labels": [label.capitalize() for label in avg_scores.keys()],
        "avg_scores_data": list(avg_scores.values()),
    }
    return render_page(request, "exam/index.html", context)


@login_required
def choose_license_type(request):
    context = {"license_types": LicenseType.objects.all()}
    return render_page(request, "exam/choose_license_type.html", context)


@login_required
def choose_questionnaire(request, license_type_id):
    license_type = get_object_or_404(LicenseType, id=license_type_id)

    ongoing_sessions = set(
        ExamSession.objects.filter(user=request.user, completed=False).values_list(
            "questionnaire_id", flat=True
        )
    )

    user_questionnaires = license_type.questionnaires.filter(user=request.user)

    available_questionnaires = license_type.questionnaires.filter(user__isnull=True)

    context = {
        "license_type": license_type,
        "questionnaires": available_questionnaires,
        "user_questionnaires": user_questionnaires,
        "ongoing_sessions": ongoing_sessions,
    }

    if request.method == "POST":
        questionnaire_id = request.POST.get("questionnaire_id")
        if questionnaire_id and int(questionnaire_id) in ongoing_sessions:
            return redirect("exam:take_exam", questionnaire_id=questionnaire_id)

        if "generate_random" in request.POST:
            title = request.POST.get("title", "").strip()
            if not title:
                messages.error(request, "Please provide a title for the questionnaire.")
            else:
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

                random_question = random.choice(questions)

                questionnaire = Questionnaire.objects.create(
                    title=title.lower(), license_type=license_type, user=request.user
                )
                questionnaire.questions.add(random_question)
                questionnaire.save()

                return redirect(
                    "exam:choose_questionnaire", license_type_id=license_type.id
                )

    return render_page(request, "exam/choose_questionnaire.html", context)


@login_required
def take_exam(request, questionnaire_id):
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)
    questions = questionnaire.questions.all().prefetch_related("options")

    exam_session, created = ExamSession.objects.get_or_create(
        user=request.user, questionnaire=questionnaire, completed=False
    )

    if exam_session.completed:
        return redirect("exam:index")

    if exam_session.is_time_up():
        exam_session.completed = True
        exam_session.end_time = timezone.now()
        exam_session.save()
        return redirect("exam:exam_result", exam_session_id=exam_session.id)

    if request.method == "POST":
        form = TakeExamForm(questions, request.POST)
        if form.is_valid():
            form.save(session=exam_session)
            exam_session.completed = True
            exam_session.save()
            return redirect("exam:review_exam", exam_session_id=exam_session.id)
        else:
            messages.error(
                request, "There was an error with your submission. Please try again."
            )

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
        "exam_session": exam_session,
    }

    return render_page(request, "exam/take_exam.html", context)


@csrf_exempt
@login_required
def mark_exam_complete(request, exam_session_id):
    if request.method == "POST":
        exam_session = get_object_or_404(
            ExamSession, id=exam_session_id, completed=False
        )
        exam_session.completed = True
        exam_session.end_time = timezone.now()
        exam_session.save()

        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid request method. Use POST."}, status=400)


@login_required
def review_exam(request, exam_session_id):
    exam_session = get_object_or_404(ExamSession, id=exam_session_id)

    if exam_session.completed:
        return redirect("exam:exam_result", exam_session_id=exam_session.id)

    if request.method == "POST":
        with transaction.atomic():
            exam_session.completed = True
            exam_session.end_time = timezone.now()
            exam_session.save()

        return redirect("exam:exam_result", exam_session_id=exam_session.id)

    answers = exam_session.answers.select_related("question", "response")

    context = {
        "questionnaire": exam_session.questionnaire,
        "answers": answers,
    }
    return render_page(request, "exam/review_exam.html", context)


@login_required
def exam_result(request, exam_session_id):
    exam_session = get_object_or_404(ExamSession, id=exam_session_id)
    user_answers = exam_session.answers.all()

    sections_data = {}
    for answer in user_answers:
        section = answer.question.section
        if section not in sections_data:
            sections_data[section] = {
                "total_questions": 0,
                "correct_count": 0,
                "wrong_count": 0,
            }

        sections_data[section]["total_questions"] += 1
        if answer.is_correct:
            sections_data[section]["correct_count"] += 1
        else:
            sections_data[section]["wrong_count"] += 1

    correct_count = user_answers.filter(is_correct=True).count()
    wrong_count = user_answers.filter(is_correct=False).count()
    total_questions = exam_session.questionnaire.questions.count()

    score_percentage = (correct_count / total_questions) * 100 if total_questions else 0

    labels = list(sections_data.keys())
    correct_data = [data["correct_count"] for data in sections_data.values()]
    wrong_data = [data["wrong_count"] for data in sections_data.values()]

    bar_chart_data = {
        "labels": labels,
        "datasets": [
            {
                "data": correct_data,
            },
            {
                "data": wrong_data,
            },
        ],
    }

    context = {
        "answers": user_answers,
        "questionnaire": exam_session.questionnaire,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "total_questions": total_questions,
        "score_percentage": score_percentage,
        "bar_chart_data": bar_chart_data,
        "exam_session": exam_session,
    }

    return render_page(request, "exam/exam_result.html", context)


@login_required
def delete_exam_session(request, exam_session_id):
    exam_session = get_object_or_404(ExamSession, id=exam_session_id)
    user_answers = exam_session.answers.all()
    correct_count = user_answers.filter(is_correct=True).count()
    total_questions = exam_session.questionnaire.questions.count()
    score_percentage = (correct_count / total_questions) * 100 if total_questions else 0

    if request.method == "POST":
        if score_percentage == 0:
            exam_session.delete()
            return redirect("exam:index")
