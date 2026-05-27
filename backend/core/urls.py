from django.urls import path

from . import views

urlpatterns = [
    path('me/', views.me, name='me'),
    path('orgs/', views.my_orgs, name='my_orgs'),
    path('debug/ensure-demo-org/', views.ensure_demo_org, name='ensure_demo_org'),
]
