from django.db import models
from django.contrib.auth.models import User


class Sections(models.TextChoices):
    CONTROLS = "CONTROLS", "Controls of motor vehicle"
    RULES = "RULES", "Rules of the road"
    LEGISLATION = "LEGISLATION", "Road traffic legislations"
    SIGNS = "SIGNS", "Signs"


class LicenseType(models.Model):
    # CODE 1, 2, 3
    title = models.CharField(max_length=20, unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return self.title


class Questionnaire(models.Model):
    title = models.CharField(max_length=20, unique=True)
    license_type = models.ForeignKey(
        LicenseType, on_delete=models.CASCADE, related_name="questionnaires"
    )
    question = models.ManyToManyField("Question", related_name="questionnaires")

    def __str__(self) -> str:
        return self.title


class Option(models.Model):
    text = models.CharField(max_length=255, unique=True, blank=True, null=True)
    image = models.ImageField(upload_to="options/", blank=True, null=True)


class Question(models.Model):
    question = models.CharField(max_length=255, unique=True)
    section = models.CharField(max_length=20, choices=Sections.choices)
    options = models.ManyToManyField(Option)
    answer = models.ForeignKey(
        "Answer", on_delete=models.PROTECT, related_name="questions"
    )

    def __str__(self) -> str:
        return self.question


class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(
        Question, on_delete=models.PROTECT, related_name="user_response_question"
    )
    response = models.ForeignKey(
        Option, on_delete=models.PROTECT, related_name="user_answer_response"
    )

    def __str__(self) -> str:
        return self.response
