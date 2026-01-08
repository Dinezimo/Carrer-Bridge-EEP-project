from django import forms
from .models import Job
from .widgets import MultipleFileInput


class JobForm(forms.ModelForm):
    skills_csv = forms.CharField(
        label="Compétences clés (séparées par des virgules)",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "python, gestion de projet, SQL"}),
    )
    education_levels_csv = forms.CharField(
        label="Niveaux d'études (séparés par des virgules)",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Licence, Master"}),
    )

    class Meta:
        model = Job
        fields = [
            "title",
            "description",
            "min_experience_years",
            "location",
            # skills & education handled via *_csv
        ]
        labels = {
            "title": "Intitulé du poste",
            "description": "Description du poste",
            "min_experience_years": "Années d'expérience minimales",
            "location": "Localisation",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["skills_csv"].initial = ", ".join(self.instance.skills or [])
            self.fields["education_levels_csv"].initial = ", ".join(
                self.instance.education_levels or []
            )

    def clean(self):
        cleaned = super().clean()
        skills_csv = cleaned.get("skills_csv", "")
        edu_csv = cleaned.get("education_levels_csv", "")

        def split_csv(v: str):
            return [s.strip() for s in v.split(",") if s.strip()]

        self.instance.skills = split_csv(skills_csv)
        self.instance.education_levels = split_csv(edu_csv)
        return cleaned


class CVUploadForm(forms.Form):
    files = forms.FileField(
        label="Importer des CV (PDF, DOCX)",
        widget=MultipleFileInput(attrs={"multiple": True}),
        help_text="Vous pouvez sélectionner plusieurs fichiers.",
    )


class CandidateApplyForm(forms.Form):
    candidate_name = forms.CharField(label="Nom complet", required=False)
    candidate_email = forms.EmailField(label="Email", required=False)
    candidate_phone = forms.CharField(label="Téléphone", required=False)
    location = forms.CharField(label="Localisation", required=False)
    linkedin_url = forms.URLField(label="Profil LinkedIn", required=False)
    cv_file = forms.FileField(label="Votre CV (PDF ou DOCX)")
