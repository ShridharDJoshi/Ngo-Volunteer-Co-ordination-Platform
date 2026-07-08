from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('<int:task_id>/', views.task_detail, name='task_detail'),
    path('assign/<int:complaint_id>/', views.assign_task, name='assign_task'),
    path('<int:task_id>/accept/', views.accept_task, name='accept_task'),
    path('<int:task_id>/decline/', views.decline_task, name='decline_task'),
    path('<int:task_id>/upload-proof/', views.upload_proof, name='upload_proof'),
    path('<int:task_id>/mark-complete/', views.mark_complete, name='mark_complete'),
    path('<int:task_id>/confirm/', views.confirm_completion, name='confirm_completion'),
    path('<int:task_id>/reject-proof/', views.reject_proof, name='reject_proof'),
]
