from django import forms

from .models import Answer, Option, Question


class TakeExamForm(forms.Form):
    def __init__(self, questions, *args, **kwargs):
        """
        Dynamically generate fields for each question passed in the constructor.
        """
        super().__init__(*args, **kwargs)
        for question in questions:
            self.fields[f"question_{question.id}"] = forms.ModelChoiceField(
                queryset=question.options.all(),
                widget=forms.RadioSelect,
                empty_label=None,
                label=question.question,
                required=True,
            )

    def save(self, user, questionnaire):
        """
        Save the user's answers and calculate the correctness.
        """
        answers = []
        for field_name, selected_option in self.cleaned_data.items():
            question_id = int(field_name.split("_")[1])
            question = Question.objects.get(id=question_id)
            answer = Answer(
                user=user,
                question=question,
                response=selected_option,
                is_correct=selected_option == question.answer,
            )
            answers.append(answer)
        Answer.objects.bulk_create(answers)  # Efficiently save answers in bulk
        return answers
