from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:notification_id>/read/', views.mark_as_read, name='mark_as_read'),
    path('<int:notification_id>/unread/', views.mark_as_unread, name='mark_as_unread'),
    path('<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('api/unread-count/', views.unread_count, name='unread_count'),
]
