from django.urls import path
from . import views

app_name = 'ngos'

urlpatterns = [
    path('', views.ngo_list, name='ngo_list'),
    path('<int:ngo_id>/', views.ngo_detail, name='ngo_detail'),
    path('<int:ngo_id>/request/', views.request_membership, name='request_membership'),
    path('membership/<int:membership_id>/approve/', views.approve_membership, name='approve_membership'),
    path('membership/<int:membership_id>/reject/', views.reject_membership, name='reject_membership'),
    path('membership/<int:membership_id>/leave/', views.leave_ngo, name='leave_ngo'),
    path('my-memberships/', views.my_memberships, name='my_memberships'),
]
