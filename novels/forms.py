from pathlib import Path

from django import forms


class NovelImportForm(forms.Form):
    title = forms.CharField(max_length=255)
    author = forms.CharField(max_length=255, required=False)
    text_file = forms.FileField(
        label="Book file",
        help_text="Upload a UTF-8 .txt/.md, PDF, or EPUB file, up to 25 MB.",
    )

    def clean_text_file(self):
        text_file = self.cleaned_data["text_file"]
        suffix = Path(text_file.name).suffix.lower()
        if suffix not in {".txt", ".md", ".pdf", ".epub"}:
            raise forms.ValidationError("Choose a .txt, .md, .pdf, or .epub file.")
        if text_file.size > 25 * 1024 * 1024:
            raise forms.ValidationError("The book file must be 25 MB or smaller.")
        return text_file


class AnalysisForm(forms.Form):
    from_chapter = forms.IntegerField(min_value=1, label="Start at chapter", initial=1)
    through_chapter = forms.IntegerField(min_value=1, label="Analyze through chapter")
