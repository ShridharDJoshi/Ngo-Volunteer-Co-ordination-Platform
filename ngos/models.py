from django.db import models
from django.conf import settings


class VolunteerProfile(models.Model):
    """Profile for volunteers with skills and experience tracking"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='volunteer_profile')
    profile_photo = models.ImageField(upload_to='profiles/volunteers/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    skills = models.TextField(blank=True, help_text='List your skills related to sanitation and community service')
    bio = models.TextField(blank=True, help_text='Tell us about yourself')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def complaint_count(self):
        """Count of complaints submitted by this volunteer"""
        return self.user.complaints.count()
    
    @property
    def task_count(self):
        """Count of tasks assigned to this volunteer"""
        return self.user.assigned_tasks.count()
    
    @property
    def completed_tasks(self):
        """Count of completed tasks"""
        return self.user.assigned_tasks.filter(status='COMPLETED').count()


class NGOProfile(models.Model):
    """Profile for NGO organizations"""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ngo_profile')
    logo = models.ImageField(upload_to='profiles/ngos/', blank=True, null=True)
    organization_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    mission = models.TextField(help_text='Your organization mission statement')
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False, help_text='NGO must be verified by admin before accessing dashboard')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.organization_name
    
    @property
    def approved_volunteers_count(self):
        """Count of approved volunteers"""
        return self.memberships.filter(status='APPROVED').count()
    
    @property
    def pending_requests_count(self):
        """Count of pending membership requests"""
        return self.memberships.filter(status='PENDING').count()


class Membership(models.Model):
    """Manages the relationship between volunteers and NGOs"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REMOVED', 'Removed'),
    ]
    
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    ngo = models.ForeignKey(NGOProfile, on_delete=models.CASCADE, related_name='memberships')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['volunteer', 'ngo']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.volunteer.username} - {self.ngo.organization_name} ({self.status})"
