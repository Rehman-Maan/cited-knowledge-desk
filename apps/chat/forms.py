from django import forms


class ChatQuestionForm(forms.Form):
    question = forms.CharField(
        label="Question",
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Ask a question about your uploaded documents",
            }
        ),
    )
