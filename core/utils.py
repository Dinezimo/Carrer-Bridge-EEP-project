import os
import re
from typing import Dict, List

from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document


def extract_text_from_pdf(path: str) -> str:
    try:
        return pdf_extract_text(path) or ""
    except Exception:
        return ""


def extract_text_from_docx(path: str) -> str:
    try:
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def extract_text_from_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    if ext == ".docx":
        return extract_text_from_docx(path)
    # Fallback: try to read as text
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def estimate_exp_years(text: str) -> int:
    # Very rough heuristic: capture patterns like "5 ans", "3 years"
    text_l = text.lower()
    candidates: List[int] = []
    for m in re.finditer(r"(\d{1,2})\s*(ans|year|years)", text_l):
        try:
            candidates.append(int(m.group(1)))
        except Exception:
            continue
    if candidates:
        return max(min(max(candidates), 40), 0)
    return 0


def analyze_cv_against_job(cv_text: str, job) -> Dict:
    text_l = (cv_text or "").lower()

    # Skills match
    job_skills = [s.strip().lower() for s in (job.skills or []) if s.strip()]
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    for s in job_skills:
        if s and s in text_l:
            matched_skills.append(s)
        else:
            missing_skills.append(s)

    skill_coverage = (len(matched_skills) / len(job_skills) * 100.0) if job_skills else 0.0

    # Experience
    exp_years = estimate_exp_years(text_l)
    min_exp = job.min_experience_years or 0
    exp_ratio = min(exp_years / max(min_exp, 1), 1.0) if min_exp > 0 else (1.0 if exp_years > 0 else 0.0)

    # Education
    edu_levels = [e.strip().lower() for e in (job.education_levels or []) if e.strip()]
    edu_match = any(e in text_l for e in edu_levels) if edu_levels else False

    # Location
    location_match = False
    if job.location:
        loc = job.location.strip().lower()
        if loc:
            location_match = loc in text_l

    # Weighted score
    score = 0.0
    score += (skill_coverage / 100.0) * 60.0  # up to 60
    score += exp_ratio * 25.0                  # up to 25
    score += (10.0 if edu_match else 0.0)      # 10
    score += (5.0 if location_match else 0.0)  # 5

    score_int = int(round(score))

    if score_int >= 80:
        category = "tres_pertinent"
    elif score_int >= 60:
        category = "pertinent"
    elif score_int >= 40:
        category = "a_revoir"
    else:
        category = "peu_pertinent"

    strengths: List[str] = []
    gaps: List[str] = []

    if matched_skills:
        strengths.append(f"Compétences correspondantes: {', '.join(matched_skills)}")
    if missing_skills:
        gaps.append(f"Compétences manquantes: {', '.join(missing_skills)}")

    if min_exp > 0:
        if exp_years >= min_exp:
            strengths.append(f"Expérience: {exp_years} ans (≥ {min_exp} ans)")
        else:
            gaps.append(f"Expérience: {exp_years} ans (< {min_exp} ans)")
    elif exp_years > 0:
        strengths.append(f"Expérience: {exp_years} ans")

    if edu_levels:
        if edu_match:
            strengths.append("Niveau d'études: correspondance trouvée")
        else:
            gaps.append("Niveau d'études: aucune correspondance explicite trouvée")

    if job.location:
        if location_match:
            strengths.append("Localisation: correspondance trouvée")
        else:
            # Not a hard gap; optional
            pass

    return {
        "score": score_int,
        "category": category,
        "exp_years": exp_years,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "strengths": strengths,
        "gaps": gaps,
    }
