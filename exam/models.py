from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from simple_history.models import HistoricalRecords


class Section(models.TextChoices):
    CONTROLS = "CONTROLS", "Controls of motor vehicle"
    RULES = "RULES", "Rules of the road"
    LEGISLATION = "LEGISLATION", "Road traffic legislations"
    SIGNS = "SIGNS", "Signs"


class LicenseType(models.Model):
    # CODE 1, 2, 3
    title = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.TextField()

    def __str__(self) -> str:
        return self.title


class Questionnaire(models.Model):
    title = models.CharField(max_length=20, unique=True)
    license_type = models.ForeignKey(
        LicenseType, on_delete=models.CASCADE, related_name="questionnaires"
    )
    questions = models.ManyToManyField("Question", related_name="questionnaires")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="generated_questionnaires",
    )
    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        if self.user:
            # Check if the user has already generated 4 questionnaires
            if Questionnaire.objects.filter(user=self.user).count() > 5:
                raise ValidationError(
                    "You can only generate a maximum of 4 questionnaires."
                )

        with transaction.atomic():
            # Make title lowercase before saving
            if self.title:
                self.title = self.title.lower()

            # Ensure the title is unique, appending incremented number if necessary
            base_title = self.title
            increment = 0

            # Check if the title already exists (excluding the current instance if updating)
            while Questionnaire.objects.filter(title=self.title).exists():
                increment += 1
                self.title = f"{base_title}-{increment}"

            # Validate questions and options (if already assigned)
            if self.pk:  # Validate only if the instance has been saved before
                for question in self.questions.all():
                    option_count = question.options.count()
                    if option_count != 3:
                        raise ValidationError(
                            f"The question '{question}' must have exactly 3 options."
                        )

            super().save(*args, **kwargs)


class Option(models.Model):
    text = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to="options/", blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.text or "Option Image"

    def clean(self) -> None:
        if not self.text and not self.image:
            raise ValidationError("Option must have either text or an image.")

    def get_related_question(self):
        """Helper method to find the related question for this option."""
        related_question = Question.objects.filter(options=self).first()
        return related_question

    def save(self, *args, **kwargs) -> None:
        if self.image and not self.text:
            # Automatically generate text for image-only options
            question = self.get_related_question()
            if question:
                option_count = question.options.count() + 1
                self.text = f"Option {option_count}"
        elif self.text:
            self.text = self.text.lower()
        self.clean()
        super().save(*args, **kwargs)


class QuestionOption(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("question", "option")


class Question(models.Model):
    question = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to="questions/", blank=True, null=True)
    section = models.CharField(max_length=20, choices=Section.choices)
    options = models.ManyToManyField(Option, through=QuestionOption)
    answer = models.ForeignKey(
        "Option", on_delete=models.PROTECT, related_name="correct_for_questions"
    )
    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.question

    def clean(self):
        if self.answer and not self.pk:
            return  # Skip validation if the question is not yet saved
        if self.answer and self.answer not in self.options.all():
            raise ValidationError("The answer must be one of the associated options.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # if self.answer and self.answer not in self.options.all():
        #     raise ValidationError("The answer must be one of the associated options.")


class Answer(models.Model):
    session = models.ForeignKey(
        "ExamSession", on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.PROTECT, related_name="answers"
    )
    response = models.ForeignKey(
        Option, on_delete=models.PROTECT, related_name="selected_by"
    )
    is_correct = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Answer for {self.session} - {self.question}: {self.response}"

    def save(self, *args, **kwargs) -> None:
        self.is_correct = self.response == self.question.answer
        super().save(*args, **kwargs)


class ExamSession(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="exam_sessions"
    )
    questionnaire = models.ForeignKey(
        Questionnaire, on_delete=models.CASCADE, related_name="sessions"
    )
    start_time = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    end_time = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    def is_time_up(self):
        return timezone.now() > self.start_time + timedelta(minutes=60)

    def mark_completed(self):
        self.completed = True
        self.end_time = timezone.now()
        self.save()

    def __str__(self):
        return f"Exam session for {self.user} on {self.questionnaire.title}"
