from django.urls import path
from . import views

urlpatterns = [
    path('', views.redirect_to_dashboard, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('jobs/new/', views.job_create, name='job_create'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/export/', views.export_shortlist_csv, name='export_shortlist_csv'),

    path('apps/<int:app_id>/toggle-shortlist/', views.toggle_shortlist, name='toggle_shortlist'),
    path('apps/<int:app_id>/reject/', views.reject_application, name='reject_application'),

    # Candidate public endpoints
    path('apply/<int:job_id>/', views.candidate_apply, name='candidate_apply'),
    path('status/<str:token>/', views.candidate_status, name='candidate_status'),
]
