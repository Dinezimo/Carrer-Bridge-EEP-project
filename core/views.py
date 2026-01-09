import secrets
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import HttpResponse, HttpRequest
from django.db.models import Q

from .models import Job, Application
from .forms import JobForm, CVUploadForm, CandidateApplyForm
from .utils import extract_text_from_upload, analyze_cv_against_job


def redirect_to_dashboard(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


def login_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        messages.error(request, "Identifiants invalides.")
    return render(request, "auth/login.html")


def logout_view(request: HttpRequest):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request: HttpRequest):
    jobs = Job.objects.filter(created_by=request.user).order_by("-created_at")
    return render(request, "dashboard.html", {"jobs": jobs})


@login_required
def job_create(request: HttpRequest):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            messages.success(request, "Offre créée.")
            return redirect("job_detail", job_id=job.id)
    else:
        form = JobForm()
    return render(request, "job_create.html", {"form": form})


@login_required
def job_detail(request: HttpRequest, job_id: int):
    job = get_object_or_404(Job, pk=job_id, created_by=request.user)

    # Upload handling
    if request.method == "POST" and request.POST.get("action") == "upload":
        upload_form = CVUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            files = request.FILES.getlist("files")
            created_count = 0
            for f in files:
                app = Application(job=job, cv_file=f)
                app.save()  # save to get file on disk
                # Extract and analyze (supports remote storage)
                text = extract_text_from_upload(app.cv_file)
                app.cv_text = text
                analysis = analyze_cv_against_job(text, job)
                app.score = analysis["score"]
                app.category = analysis["category"]
                app.exp_years = analysis["exp_years"]
                app.matched_skills = analysis["matched_skills"]
                app.missing_skills = analysis["missing_skills"]
                app.strengths = analysis["strengths"]
                app.gaps = analysis["gaps"]
                app.save()
                created_count += 1
            messages.success(request, f"{created_count} CV(s) importé(s) et analysé(s).")
            return redirect("job_detail", job_id=job.id)
    else:
        upload_form = CVUploadForm()

    # Filters
    qs = job.applications.all().order_by("-score", "-created_at")
    category = request.GET.get("category")
    min_score = request.GET.get("min_score")
    skill = request.GET.get("skill")
    only_shortlist = request.GET.get("only_shortlist") == "1"

    if category:
        qs = qs.filter(category=category)
    if min_score:
        try:
            qs = qs.filter(score__gte=int(min_score))
        except ValueError:
            pass
    if skill:
        skl = (skill or "").strip().lower()
        if skl:
            qs = qs.filter(Q(matched_skills__contains=[skl]) | Q(cv_text__icontains=skl))
    if only_shortlist:
        qs = qs.filter(is_shortlisted=True)

    return render(
        request,
        "job_detail.html",
        {
            "job": job,
            "applications": qs,
            "upload_form": upload_form,
            "filters": {
                "category": category or "",
                "min_score": min_score or "",
                "skill": skill or "",
                "only_shortlist": only_shortlist,
            },
            "apply_link": request.build_absolute_uri(reverse("candidate_apply", args=[job.id])),
        },
    )


@login_required
def toggle_shortlist(request: HttpRequest, app_id: int):
    app = get_object_or_404(Application, pk=app_id, job__created_by=request.user)
    app.is_shortlisted = not app.is_shortlisted
    app.status = "shortlisted" if app.is_shortlisted else "in_review"
    app.save()
    return redirect("job_detail", job_id=app.job.id)


@login_required
def export_shortlist_csv(request: HttpRequest, job_id: int):
    import csv
    job = get_object_or_404(Job, pk=job_id, created_by=request.user)
    apps = job.applications.filter(is_shortlisted=True).order_by("-score")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename=shortlist_job_{job_id}.csv"
    writer = csv.writer(response)
    writer.writerow([
        "Candidate",
        "Email",
        "Phone",
        "Score",
        "Category",
        "Matched Skills",
        "Missing Skills",
        "Strengths",
        "Gaps",
        "CV File",
    ])
    for a in apps:
        writer.writerow([
            a.candidate_name,
            a.candidate_email,
            a.candidate_phone,
            a.score,
            a.get_category_display(),
            ", ".join(a.matched_skills or []),
            ", ".join(a.missing_skills or []),
            "; ".join(a.strengths or []),
            "; ".join(a.gaps or []),
            a.cv_file.url,
        ])
    return response


def _gen_unique_token() -> str:
    return secrets.token_hex(16)


def _ensure_unique_token() -> str:
    token = _gen_unique_token()
    while Application.objects.filter(status_token=token).exists():
        token = _gen_unique_token()
    return token


def _compose_candidate_feedback(analysis: dict, job: Job) -> str:
    parts = [
        "Merci d'avoir postulé. Voici un retour préliminaire généré automatiquement:",
    ]
    if analysis.get("matched_skills"):
        parts.append("Points forts: " + ", ".join(analysis["matched_skills"]))
    if analysis.get("missing_skills"):
        parts.append("Compétences à renforcer: " + ", ".join(analysis["missing_skills"]))
    exp = analysis.get("exp_years", 0)
    if job.min_experience_years:
        if exp < job.min_experience_years:
            parts.append(
                f"Expérience indiquée: {exp} an(s) (min. souhaité: {job.min_experience_years})."
            )
    return "\n".join(parts)


def candidate_apply(request: HttpRequest, job_id: int):
    job = get_object_or_404(Job, pk=job_id)
    if request.method == "POST":
        form = CandidateApplyForm(request.POST, request.FILES)
        if form.is_valid():
            app = Application(
                job=job,
                candidate_name=form.cleaned_data.get("candidate_name", ""),
                candidate_email=form.cleaned_data.get("candidate_email", ""),
                candidate_phone=form.cleaned_data.get("candidate_phone", ""),
                location=form.cleaned_data.get("location", ""),
                linkedin_url=form.cleaned_data.get("linkedin_url", ""),
                cv_file=form.cleaned_data["cv_file"],
                status="in_review",
            )
            app.save()
            text = extract_text_from_upload(app.cv_file)
            app.cv_text = text
            analysis = analyze_cv_against_job(text, job)
            app.score = analysis["score"]
            app.category = analysis["category"]
            app.exp_years = analysis["exp_years"]
            app.matched_skills = analysis["matched_skills"]
            app.missing_skills = analysis["missing_skills"]
            app.strengths = analysis["strengths"]
            app.gaps = analysis["gaps"]
            app.status_token = _ensure_unique_token()
            app.feedback_suggestions = _compose_candidate_feedback(analysis, job)
            app.save()
            return redirect("candidate_status", token=app.status_token)
    else:
        form = CandidateApplyForm()
    return render(request, "candidate_apply.html", {"job": job, "form": form})


def candidate_status(request: HttpRequest, token: str):
    app = get_object_or_404(Application, status_token=token)
    if app.is_shortlisted:
        status_label = "Présélectionné"
        status_desc = "Félicitations, votre candidature a été présélectionnée. Un recruteur vous contactera."
    elif app.status == "rejected":
        status_label = "Non retenu pour l'instant"
        status_desc = (
            "Merci pour votre intérêt. Nous partageons ces éléments pour vous aider à progresser."
        )
    else:
        status_label = "En cours d'analyse"
        status_desc = "Votre candidature a bien été reçue et est en cours d'évaluation."

    return render(
        request,
        "candidate_status.html",
        {
            "app": app,
            "status_label": status_label,
            "status_desc": status_desc,
        },
    )


@login_required
def reject_application(request: HttpRequest, app_id: int):
    app = get_object_or_404(Application, pk=app_id, job__created_by=request.user)
    reason = request.GET.get(
        "reason",
        "Merci pour votre candidature. Le profil ne correspond pas suffisamment aux critères du poste à ce stade.",
    )
    app.is_shortlisted = False
    app.status = "rejected"
    app.feedback_reason = reason
    # If no suggestions yet, propose basic guidance based on missing skills
    if not app.feedback_suggestions:
        if app.missing_skills:
            app.feedback_suggestions = (
                "Pour augmenter vos chances, travaillez les compétences suivantes: "
                + ", ".join(app.missing_skills)
            )
        else:
            app.feedback_suggestions = (
                "Merci pour votre intérêt. Nous vous encourageons à continuer de postuler aux offres pertinentes."
            )
    app.save()
    messages.info(request, "Candidature marquée comme non retenue.")
    return redirect("job_detail", job_id=app.job.id)
