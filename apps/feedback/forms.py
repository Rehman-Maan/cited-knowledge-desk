from django import forms

from apps.feedback.models import AnswerFeedback


class AnswerFeedbackForm(forms.ModelForm):
    class Meta:
        model = AnswerFeedback
        fields = ["rating", "failure_tag", "comment"]
        widgets = {
            "rating": forms.RadioSelect,
            "failure_tag": forms.Select,
            "comment": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional note for review",
                }
            ),
        }

    def clean_failure_tag(self):
        failure_tag = self.cleaned_data.get("failure_tag")
        rating = self.cleaned_data.get("rating")
        if rating == AnswerFeedback.Rating.UP:
            return ""
        return failure_tag
