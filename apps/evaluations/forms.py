from django import forms


class EvaluationRunForm(forms.Form):
    name = forms.CharField(max_length=180, required=False)
    dataset_path = forms.CharField(
        initial="eval/gold_questions.yml",
        max_length=240,
    )
    retrieval_top_k = forms.IntegerField(min_value=1, max_value=20, initial=8)
