from django import forms
from django.utils.safestring import mark_safe

from .models import Answer, Question


class TakeExamForm(forms.Form):
    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for question in questions:
            # Generate the image HTML if available
            image_html = (
                f'<img src="{question.image.url}" alt="{question.question}" />'
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

    def save(self, session) -> None:
        answers_to_create = []
        answers_to_update = []

        # Fetch existing answers in a single query
        existing_answers = {
            (answer.question_id, answer.session_id): answer
            for answer in Answer.objects.filter(session=session)
        }

        for field_name, selected_option in self.cleaned_data.items():
            # Extract question ID from the field name
            question_id = int(field_name.split("_")[1])
            question = Question.objects.get(id=question_id)

            answer_key = (question_id, session.id)

            if answer_key in existing_answers:
                # Update existing answer
                answer = existing_answers[answer_key]
                answer.response = selected_option
                answer.is_correct = selected_option == question.answer
                answers_to_update.append(answer)
            else:
                # Create new answer
                answers_to_create.append(
                    Answer(
                        session=session,
                        question=question,
                        response=selected_option,
                        is_correct=selected_option == question.answer,
                    )
                )

        # Bulk create and update in a single query each
        if answers_to_create:
            Answer.objects.bulk_create(answers_to_create)

        if answers_to_update:
            Answer.objects.bulk_update(answers_to_update, ["response", "is_correct"])
