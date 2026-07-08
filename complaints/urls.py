from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('', views.complaint_list, name='complaint_list'),
    path('create/', views.complaint_create, name='complaint_create'),
    path('<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('<int:complaint_id>/accept/', views.accept_complaint, name='accept_complaint'),
    path('<int:complaint_id>/reject/', views.reject_complaint, name='reject_complaint'),
    path('<int:complaint_id>/request-help/', views.request_volunteer_help, name='request_help'),
    path('help-request/<int:request_id>/accept/', views.accept_help_request, name='accept_help_request'),
    path('help-request/<int:request_id>/decline/', views.decline_help_request, name='decline_help_request'),
]
