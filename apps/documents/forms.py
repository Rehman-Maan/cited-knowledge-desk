from pathlib import Path

from django import forms
from django.conf import settings

from apps.documents.models import Document


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "file"]

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_DOCUMENT_EXTENSIONS)
            raise forms.ValidationError(f"Upload a supported file type: {allowed}.")

        if uploaded_file.size > settings.MAX_DOCUMENT_UPLOAD_SIZE:
            max_mb = settings.MAX_DOCUMENT_UPLOAD_SIZE // (1024 * 1024)
            raise forms.ValidationError(f"Upload a file smaller than {max_mb} MB.")

        return uploaded_file

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Enter a document title.")
        return title
