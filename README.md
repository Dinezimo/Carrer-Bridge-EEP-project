# CV Assistant (MVP)

Assistant de tri de CV pour recruteurs (RH) avec IA simulée. Conçu pour réduire le temps de présélection et offrir un feedback simple aux candidats. Pile technique: Django + SQLite + pdfminer.six + python-docx.

## Principes
- IA assistante, décision finale humaine.
- Transparence: explications du score.
- Respect du candidat: lien de statut + retour courtois.
- Simplicité: pas de configuration complexe.

## Prérequis
- Python 3.10+ (testé avec 3.11)

## Installation
```bash
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
```

## Démarrage (dev)
```bash
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py bootstrap_demo  # crée l'utilisateur demo/demo12345
./.venv/bin/python manage.py runserver 0.0.0.0:8000
```

Ouvrir http://127.0.0.1:8000 et se connecter avec:
- utilisateur: `demo`
- mot de passe: `demo12345`

## Parcours RH
1. Créer une offre: `Jobs > Créer une offre` (définir compétences, exp mini, études, localisation).
2. Importer des CV (PDF/DOCX) depuis la page de l’offre.
3. Voir l’analyse: score, catégorie, compétences matchées/manquantes, exp estimée.
4. Filtrer, ajouter/retirer de la shortlist, exporter la shortlist en CSV.
5. Partager le **lien public de candidature** depuis la page de l’offre.

## Parcours Candidat
- Lien public: `/apply/<job_id>/` (affiché sur la page de l’offre côté RH).
- Déposer le CV sans ressaisie obligatoire.
- Être redirigé vers une page de **statut public** `/status/<token>/` avec feedback courtois.

## Analyse simulée (MVP)
- Extraction texte:
  - PDF: `pdfminer.six`
  - DOCX: `python-docx`
- Scoring:
  - 60% compétences (mots-clés)
  - 25% années d’expérience (heuristique)
  - 10% niveau d’études
  - 5% localisation
- Catégories: Très pertinent / Pertinent / À revoir / Peu pertinent
- Explications: points forts + écarts (compétences manquantes, expérience, etc.).

## Données (Firestore ≠ ici)
- Base: SQLite
- Modèles: `Job`, `Application` (voir `core/models.py`)
- Fichiers CV: `media/cvs/`

## Sécurité (dev)
- Projet en `DEBUG=True`, ne pas utiliser en production tel quel.
- Règles d’accès:
  - RH authentifiés: gestion des offres et candidatures de leurs propres offres.
  - Portail candidat: accès public **uniquement** via lien de statut.
- Pas d’emailing en MVP.

## Personnalisation
- Styles: `static/styles.css`
- Templates: `templates/` (base, auth, dashboard, job pages, candidate pages)
- Scores/pondérations: `core/utils.py` (`analyze_cv_against_job`)

## Roadmap (post-MVP)
- Notes RH par candidat, comparaison côte-à-côte.
- Modèles de critères par type de poste.
- Historique et tableaux de bord.
- Authentification RH plus complète (inscription, reset mot de passe).
- Intégration cloud storage (S3) et base SQL/NoSQL.

## Licence
MVP démonstratif. Usage interne/POC.
