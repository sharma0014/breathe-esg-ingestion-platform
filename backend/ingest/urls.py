from django.urls import path

from . import views

urlpatterns = [
    path('orgs/<slug:org_slug>/sources/', views.sources, name='sources'),
    path('orgs/<slug:org_slug>/jobs/', views.jobs, name='jobs'),
    path('orgs/<slug:org_slug>/jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('orgs/<slug:org_slug>/jobs/<int:job_id>/records/', views.job_records, name='job_records'),
    path('orgs/<slug:org_slug>/jobs/<int:job_id>/errors/', views.job_errors, name='job_errors'),
    path('orgs/<slug:org_slug>/ingest/upload/', views.upload_and_ingest, name='upload_and_ingest'),
    path('orgs/<slug:org_slug>/records/<int:record_id>/', views.update_record, name='update_record'),
    path('orgs/<slug:org_slug>/records/<int:record_id>/approve/', views.approve_record, name='approve_record'),
    path('orgs/<slug:org_slug>/jobs/<int:job_id>/lock/', views.lock_job, name='lock_job'),
]
