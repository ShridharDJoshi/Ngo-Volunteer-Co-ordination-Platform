from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Custom user model with role-based access control"""
    
    ROLE_CHOICES = [
        ('VOLUNTEER', 'Volunteer'),
        ('NGO', 'NGO'),
        ('ADMIN', 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='VOLUNTEER')
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_volunteer(self):
        return self.role == 'VOLUNTEER'
    
    def is_ngo(self):
        return self.role == 'NGO'
    
    def is_admin_user(self):
        return self.role == 'ADMIN' or self.is_superuser
