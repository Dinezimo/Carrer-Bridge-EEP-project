from django.db import models
from django.contrib.auth.models import User


class Job(models.Model):
    STATUS_CHOICES = (
        ("open", "Open"),
        ("closed", "Closed"),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)  # list of strings
    min_experience_years = models.IntegerField(default=0)
    education_levels = models.JSONField(default=list, blank=True)  # list of strings
    location = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class Application(models.Model):
    CATEGORY_CHOICES = (
        ("tres_pertinent", "Très pertinent"),
        ("pertinent", "Pertinent"),
        ("a_revoir", "À revoir"),
        ("peu_pertinent", "Peu pertinent"),
    )

    STATUS_CHOICES = (
        ("received", "Received"),
        ("in_review", "In review"),
        ("shortlisted", "Shortlisted"),
        ("rejected", "Rejected"),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")

    candidate_name = models.CharField(max_length=200, blank=True)
    candidate_email = models.EmailField(blank=True)
    candidate_phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=120, blank=True)
    linkedin_url = models.URLField(blank=True)

    cv_file = models.FileField(upload_to="cvs/")
    cv_text = models.TextField(blank=True)

    score = models.IntegerField(default=0)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="a_revoir")
    exp_years = models.IntegerField(default=0)
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    gaps = models.JSONField(default=list, blank=True)

    is_shortlisted = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="received")

    feedback_reason = models.TextField(blank=True)
    feedback_suggestions = models.TextField(blank=True)

    status_token = models.CharField(max_length=64, blank=True, null=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        base = self.candidate_name or self.candidate_email or self.cv_file.name
        return f"{base} -> {self.job.title}"

# Create your models here.
