import random
from collections import defaultdict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import TakeExamForm
from .models import ExamSession, LicenseType, Question, Questionnaire


@login_required
def index(request) -> HttpResponse:
    # Retrieve all the completed exams for the logged-in user
    exams = (
        ExamSession.objects.filter(
            user=request.user, completed=True
        )  # Filter completed exams for the user
        .select_related(
            "questionnaire"
        )  # Optimizes query by fetching related questionnaire in one go
        .prefetch_related(
            "answers", "questionnaire__questions"
        )  # Prefetch related answers and questions for each exam session
        .annotate(
            # Annotating the number of correct answers and the total number of questions in each exam
            correct_count=Count(
                "answers", filter=F("answers__is_correct")
            ),  # Count correct answers
            total_questions=Count(
                "questionnaire__questions"
            ),  # Count all questions in the questionnaire
        )
    )

    # List to store exam data
    exams_data = []

    # Dictionary to store scores for each questionnaire
    questionnaire_scores = defaultdict(list)

    # Loop through each exam session to process data
    for exam in exams:
        correct_count = exam.correct_count  # Get the number of correct answers
        total_questions = (
            exam.total_questions
        )  # Get the total number of questions in the exam
        # Calculate the percentage score, if there are questions
        score_percentage = (
            (correct_count / total_questions) * 100 if total_questions > 0 else 0
        )

        # Store the exam data in the exams_data list
        exams_data.append(
            {
                "exam": exam,
                "questionnaire": exam.questionnaire,  # The questionnaire associated with the exam
                "correct_count": correct_count,
                "total_questions": total_questions,
                "score_percentage": score_percentage,  # Score percentage for the exam
                "start_time": exam.start_time,  # Exam start time
            }
        )

        # Append the score to the dictionary based on the questionnaire title
        questionnaire_scores[exam.questionnaire.title].append(score_percentage)

    # Calculate the average score for each questionnaire
    avg_scores = {
        questionnaire: sum(scores) / len(scores)
        for questionnaire, scores in questionnaire_scores.items()  # Calculate average of all scores for each questionnaire
    }

    # Prepare context for rendering in the template
    context = {
        "exams_data": exams_data,  # Exam data for the user
        # Capitalize each questionnaire title and prepare it as a label for the chart
        "avg_scores_labels": [label.capitalize() for label in avg_scores.keys()],
        # Average scores as a list to plot in a graph/chart
        "avg_scores_data": list(avg_scores.values()),
    }

    # Render the "exam/index.html" template with the context
    return render(request, "exam/index.html", context)


@login_required
def choose_license_type(request) -> HttpResponse:
    context = {"license_types": LicenseType.objects.all()}
    return render(request, "exam/choose_license_type.html", context)


@login_required
def choose_questionnaire(request, license_type_id) -> HttpResponse:
    # Retrieve the LicenseType object using the provided license_type_id, or return a 404 if not found
    license_type = get_object_or_404(LicenseType, id=license_type_id)

    # Get all ongoing exam sessions for the current user (sessions that are not completed yet)
    ongoing_sessions = set(
        ExamSession.objects.filter(user=request.user, completed=False).values_list(
            "questionnaire_id", flat=True
        )
    )

    # Get the questionnaires that the user has already created for this license type
    user_questionnaires = license_type.questionnaires.filter(user=request.user)

    # Get questionnaires for this license type that are not yet assigned to any user
    available_questionnaires = license_type.questionnaires.filter(user__isnull=True)

    # Prepare the context data to pass to the template
    context = {
        "license_type": license_type,  # License type to display
        "questionnaires": available_questionnaires,  # Questionnaires available for selection
        "user_questionnaires": user_questionnaires,  # Questionnaires the user has already created
        "ongoing_sessions": ongoing_sessions,  # Ongoing exam sessions for the user
    }

    # If the form is submitted via POST (e.g., user selects a questionnaire or creates a new one)
    if request.method == "POST":
        # Check if the user selected an existing questionnaire to continue from ongoing sessions
        questionnaire_id = request.POST.get("questionnaire_id")
        if questionnaire_id and int(questionnaire_id) in ongoing_sessions:
            # Redirect to the 'take_exam' page with the selected questionnaire
            return redirect("exam:take_exam", questionnaire_id=questionnaire_id)

        # Check if the user clicked on the 'Generate Random' button to create a new questionnaire
        if "generate_random" in request.POST:
            title = request.POST.get(
                "title", ""
            ).strip()  # Get the title for the new questionnaire
            # If no title is provided, show an error message
            if not title:
                messages.error(request, "Please provide a title for the questionnaire.")
            else:
                # Get all questions related to the current license type
                questions = Question.objects.filter(
                    questionnaires__license_type=license_type
                )
                # If there are no questions available, show an error message
                if not questions.exists():
                    messages.error(
                        request, "No questions available for this license type."
                    )
                    # Redirect to the same page if no questions are available
                    return redirect(
                        "exam:choose_questionnaire", license_type_id=license_type.id
                    )

                # Select a random question from the available questions
                random_question = random.choice(questions)

                # Create a new questionnaire with the specified title, associate it with the license type, and assign the current user
                questionnaire = Questionnaire.objects.create(
                    title=title.lower(), license_type=license_type, user=request.user
                )
                # Add the randomly selected question to the new questionnaire
                questionnaire.questions.add(random_question)
                # Save the new questionnaire
                questionnaire.save()

                # Redirect to the same page to show the newly created questionnaire
                return redirect(
                    "exam:choose_questionnaire", license_type_id=license_type.id
                )

    # Render the template with the context data
    return render(request, "exam/choose_questionnaire.html", context)


@login_required
def take_exam(request, questionnaire_id) -> HttpResponse:
    # Retrieve the questionnaire object using the provided questionnaire_id, or return a 404 if not found
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id)

    # Retrieve all the questions for this questionnaire and prefetch related options to optimize DB queries
    questions = questionnaire.questions.all().prefetch_related("options")

    # Try to get an existing exam session for the user and questionnaire, or create one if it doesn't exist
    exam_session, created = ExamSession.objects.get_or_create(
        user=request.user, questionnaire=questionnaire, completed=False
    )

    # If the exam session is already completed, redirect the user to the index page
    if exam_session.completed:
        return redirect("exam:index")

    # Check if the time for the exam session is up (60 minutes after start time)
    if exam_session.is_time_up():
        # Mark the session as completed and save the end time
        exam_session.completed = True
        exam_session.end_time = timezone.now()
        exam_session.save()
        # Redirect to the exam result page
        return redirect("exam:exam_result", exam_session_id=exam_session.id)

    # Handle form submission when the user submits their answers (POST request)
    if request.method == "POST":
        # Create a form instance with the questions and POST data
        form = TakeExamForm(questions, request.POST)

        # Check if the form is valid (all answers are correct and submitted properly)
        if form.is_valid():
            # Save the form data, associating the answers with the current exam session
            form.save(session=exam_session)
            exam_session.save()

            # Redirect to the review exam page to review the answers
            return redirect("exam:review_exam", exam_session_id=exam_session.id)
        else:
            # If the form is not valid, show an error message
            messages.error(
                request, "There was an error with your submission. Please try again."
            )

    # If the request method is not POST, instantiate a new form with the questions (GET request)
    else:
        form = TakeExamForm(questions)

    # Calculate the remaining time for the exam session (60 minutes from the start time)
    time_left = max(
        (exam_session.start_time + timedelta(minutes=60)) - timezone.now(),
        timedelta(0),  # Ensure time_left is never negative
    )

    # Prepare the context data to pass to the template
    context = {
        "questionnaire": questionnaire,  # The questionnaire being taken
        "form": form,  # The form containing the questions and answers
        "time_left": time_left,  # The remaining time for the exam
        "exam_session": exam_session,  # The current exam session
    }

    # Render the take_exam.html template with the context data
    return render(request, "exam/take_exam.html", context)


# This view marks an exam session as complete when a POST request is made.
@csrf_exempt  # This decorator disables CSRF protection for this view (usually not recommended unless necessary).
@login_required  # Ensures that only authenticated users can access this view.
def mark_exam_complete(request, exam_session_id) -> JsonResponse:
    # Check if the request method is POST (only POST requests will be processed)
    if request.method == "POST":
        # Retrieve the exam session object by its ID. It must be incomplete (completed=False).
        exam_session = get_object_or_404(
            ExamSession, id=exam_session_id, completed=False
        )

        # Mark the exam session as completed
        exam_session.completed = True

        # Set the end time of the exam session to the current time
        exam_session.end_time = timezone.now()

        # Save the changes to the database
        exam_session.save()

        # Return a JSON response indicating success
        return JsonResponse({"success": True})

    # If the request method is not POST, return an error response with status 400
    return JsonResponse({"error": "Invalid request method. Use POST."}, status=400)


# This view allows the user to review their exam answers and mark the exam as completed.
@login_required  # Ensures that only authenticated users can access this view.
def review_exam(request, exam_session_id) -> HttpResponse:
    # Retrieve the ExamSession object by its ID. If it doesn't exist, it will return a 404 error.
    exam_session = get_object_or_404(ExamSession, id=exam_session_id)

    # If the exam session is already marked as completed, redirect to the exam result page.
    if exam_session.completed:
        return redirect("exam:exam_result", exam_session_id=exam_session.id)

    # Handle POST request: this will mark the exam as completed and save the current time as the end time.
    if request.method == "POST":
        with transaction.atomic():  # Start a transaction to ensure the operation is atomic (all-or-nothing).
            exam_session.completed = True  # Mark the exam as completed.
            exam_session.end_time = (
                timezone.now()
            )  # Set the current time as the end time.
            exam_session.save()  # Save the changes to the database.

        # After marking the exam as completed, redirect the user to the exam result page.
        return redirect("exam:exam_result", exam_session_id=exam_session.id)

    # Retrieve all answers for this exam session, along with their related question and response.
    answers = exam_session.answers.select_related("question", "response")

    # Prepare the context for the template.
    context = {
        "questionnaire": exam_session.questionnaire,  # Pass the associated questionnaire.
        "answers": answers,  # Pass the user's answers.
    }

    # Render the review_exam.html template with the context data.
    return render(request, "exam/review_exam.html", context)


@login_required  # Ensures that only authenticated users can access this view.
def exam_result(request, exam_session_id) -> HttpResponse:
    # Retrieve the ExamSession object by its ID. If it doesn't exist, it will return a 404 error.
    exam_session = get_object_or_404(ExamSession, id=exam_session_id)

    # Retrieve all answers related to the exam session.
    user_answers = exam_session.answers.all()

    # Initialize a dictionary to store data about sections.
    sections_data = {}

    # Loop through each answer to calculate data per section.
    for answer in user_answers:
        section = answer.question.section  # Get the section of the question.

        # If the section is not already in the sections_data dictionary, add it.
        if section not in sections_data:
            sections_data[section] = {
                "total_questions": 0,  # Keep track of the total number of questions in this section.
                "correct_count": 0,  # Keep track of the correct answers in this section.
                "wrong_count": 0,  # Keep track of the wrong answers in this section.
            }

        # Update the total questions for this section.
        sections_data[section]["total_questions"] += 1

        # If the answer is correct, increment the correct count, otherwise increment the wrong count.
        if answer.is_correct:
            sections_data[section]["correct_count"] += 1
        else:
            sections_data[section]["wrong_count"] += 1

    # Count the total number of correct and incorrect answers.
    correct_count = user_answers.filter(is_correct=True).count()
    wrong_count = user_answers.filter(is_correct=False).count()

    # Calculate the total number of questions in the questionnaire.
    total_questions = exam_session.questionnaire.questions.count()

    # Calculate the score as a percentage.
    score_percentage = (correct_count / total_questions) * 100 if total_questions else 0

    # Prepare the data for the bar chart.
    # The labels are the section names (keys from sections_data).
    labels = list(sections_data.keys())

    # The correct_data list contains the correct answer count for each section.
    correct_data = [data["correct_count"] for data in sections_data.values()]

    # The wrong_data list contains the wrong answer count for each section.
    wrong_data = [data["wrong_count"] for data in sections_data.values()]

    # Prepare the bar chart data in the format required by the charting library.
    bar_chart_data = {
        "labels": labels,  # The labels for each section.
        "datasets": [  # The datasets for correct and wrong answers.
            {
                "data": correct_data,  # Correct answers.
            },
            {
                "data": wrong_data,  # Wrong answers.
            },
        ],
    }

    # Prepare the context dictionary, which will be passed to the template.
    context = {
        "answers": user_answers,  # The user's answers.
        "questionnaire": exam_session.questionnaire,  # The questionnaire associated with the exam session.
        "correct_count": correct_count,  # Total correct answers.
        "wrong_count": wrong_count,  # Total wrong answers.
        "total_questions": total_questions,  # Total number of questions.
        "score_percentage": score_percentage,  # The score percentage.
        "bar_chart_data": bar_chart_data,  # The data for the bar chart.
        "exam_session": exam_session,  # The current exam session.
    }

    # Render the exam result page with the provided context.
    return render(request, "exam/exam_result.html", context)


@login_required
def delete_exam_session(request, exam_session_id) -> HttpResponse:
    # Retrieve the ExamSession by its ID, or raise a 404 error if not found.
    exam_session = get_object_or_404(ExamSession, id=exam_session_id)

    # Retrieve all answers associated with this exam session.
    user_answers = exam_session.answers.all()

    # Check if the exam session has no answers (i.e., it's not started or answered).
    if user_answers.count() == 0:
        # If there are no answers, delete the exam session.
        exam_session.delete()

        # Redirect the user back to the exam index page.
        return redirect("exam:index")
