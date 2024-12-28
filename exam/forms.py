from django import forms
from django.utils.safestring import mark_safe
from .models import Answer, Question


class TakeExamForm(forms.Form):
    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for question in questions:
            image_html = (
                f'<img src="{question.image.url}" alt="{question.question}" class="question-image" />'
                if question.image
                else ""
            )
            label_html = f"<span>{question.question}</span>{image_html}"
            self.fields[f"question_{question.id}"] = forms.ModelChoiceField(
                queryset=question.options.all(),
                widget=forms.RadioSelect,
                # label=question.question,
                label=mark_safe(label_html),
                required=True,
            )

    def save(self, session):
        for field_name, selected_option in self.cleaned_data.items():
            question_id = int(field_name.split("_")[1])
            question = Question.objects.get(id=question_id)
            Answer.objects.create(
                session=session, question=question, response=selected_option
            )
