from django import forms


class RetrievalSearchForm(forms.Form):
    q = forms.CharField(
        label="Search query",
        max_length=500,
        widget=forms.TextInput(attrs={"placeholder": "Search ready document chunks"}),
    )
    top_k = forms.IntegerField(label="Top K", min_value=1, max_value=20, initial=8)
