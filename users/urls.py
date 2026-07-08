from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/choice/', views.login_choice_view, name='login_choice'),
    path('register/choice/', views.register_choice_view, name='register_choice'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]
