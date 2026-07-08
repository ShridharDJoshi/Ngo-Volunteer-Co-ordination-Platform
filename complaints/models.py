from django.db import models
from django.conf import settings
from ngos.models import NGOProfile


class Complaint(models.Model):
    """Complaint model for tracking sanitation issues"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    
    CATEGORY_CHOICES = [
        ('WASTE_MANAGEMENT', 'Waste Management'),
        ('DRAINAGE', 'Drainage Issue'),
        ('PUBLIC_TOILET', 'Public Toilet'),
        ('STREET_CLEANING', 'Street Cleaning'),
        ('WATER_SUPPLY', 'Water Supply'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=300)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    image = models.ImageField(upload_to='complaints/', blank=True, null=True)
    
    # Relationships
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    linked_ngo = models.ForeignKey(NGOProfile, on_delete=models.CASCADE, related_name='complaints', null=True, blank=True)
    
    # Volunteer assignment tracking
    assigned_ngo = models.ForeignKey(NGOProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints', help_text='NGO handling this complaint')
    volunteers_helping = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='helping_complaints', help_text='Volunteers helping with this complaint')
    is_assigned = models.BooleanField(default=False, help_text='Whether complaint has been assigned to volunteers')
    
    # Status tracking
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def get_progress_percentage(self):
        """Calculate progress percentage based on status"""
        status_progress = {
            'PENDING': 20,
            'ACCEPTED': 40,
            'TASK_ASSIGNED': 60,
            'IN_PROGRESS': 80,
            'COMPLETED': 100,
            'REJECTED': 0,
        }
        return status_progress.get(self.status, 0)
    
    def get_progress_stages(self):
        """Get list of progress stages with completion status"""
        stages = [
            {'name': 'Pending', 'status': 'PENDING'},
            {'name': 'Accepted', 'status': 'ACCEPTED'},
            {'name': 'Task Assigned', 'status': 'TASK_ASSIGNED'},
            {'name': 'In Progress', 'status': 'IN_PROGRESS'},
            {'name': 'Completed', 'status': 'COMPLETED'},
        ]
        
        status_order = ['PENDING', 'ACCEPTED', 'TASK_ASSIGNED', 'IN_PROGRESS', 'COMPLETED']
        
        if self.status == 'REJECTED':
            return [
                {'name': 'Pending', 'status': 'PENDING', 'completed': True},
                {'name': 'Rejected', 'status': 'REJECTED', 'completed': True, 'rejected': True},
            ]
        
        try:
            current_index = status_order.index(self.status)
        except ValueError:
            current_index = -1
        
        for i, stage in enumerate(stages):
            stage['completed'] = i <= current_index
            stage['active'] = i == current_index
        
        return stages


class ComplaintStatusLog(models.Model):
    """Track status changes for complaints"""
    
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=15, blank=True)
    new_status = models.CharField(max_length=15)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.complaint.title} - {self.old_status} → {self.new_status}"


class ComplaintHelpRequest(models.Model):
    """Track when NGOs request volunteer help for complaints"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
    ]
    
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='help_requests')
    ngo = models.ForeignKey(NGOProfile, on_delete=models.CASCADE, related_name='help_requests')
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='help_requests_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    message = models.TextField(blank=True, help_text='Message to volunteer')
    
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['complaint', 'volunteer']
    
    def __str__(self):
        return f"Help request for {self.complaint.title} - {self.volunteer.username} ({self.status})"
