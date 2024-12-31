from django import forms
from django.utils.safestring import mark_safe

from .models import Answer, Question


class TakeExamForm(forms.Form):
    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for question in questions:
            # Generate the image HTML if available
            image_html = (
                f'<img src="{question.image.url}" alt="{question.question}" class="question-image" />'
                if question.image
                else ""
            )
            # Generate the label HTML for the question
            label_html = f"<span>{question.question}</span>{image_html}"

            # Add a ModelChoiceField for each question's options
            self.fields[f"question_{question.id}"] = forms.ModelChoiceField(
                queryset=question.options.all(),
                widget=forms.RadioSelect,
                label=mark_safe(label_html),  # Ensure safe HTML rendering
                required=True,
            )

    def save(self, session):
        answers = []
        for field_name, selected_option in self.cleaned_data.items():
            # Extract question ID from the field name
            question_id = int(field_name.split("_")[1])
            question = Question.objects.get(id=question_id)

            # Answer.objects.create(
            #     session=session, question=question, response=selected_option
            # )

            # Determine if the selected option is the correct answer
            is_correct = selected_option == question.answer

            # Add the Answer instance to the list (bulk creation can be more efficient)
            answers.append(
                Answer(
                    session=session,
                    question=question,
                    response=selected_option,
                    is_correct=is_correct,
                )
            )

        # Bulk create answers to minimize database hits
        Answer.objects.bulk_create(answers)
