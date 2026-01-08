from django.contrib import admin
from .models import Job, Application


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "created_by", "created_at")
    search_fields = ("title", "description", "location")
    list_filter = ("status", "created_at")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "candidate_name", "score", "category", "is_shortlisted", "created_at")
    search_fields = ("candidate_name", "candidate_email", "cv_file")
    list_filter = ("category", "is_shortlisted", "status", "created_at")
