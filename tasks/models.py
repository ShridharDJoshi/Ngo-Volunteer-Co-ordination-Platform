from django.db import models
from django.conf import settings
from complaints.models import Complaint


class Task(models.Model):
    """Task assignment model for complaint resolution"""
    
    STATUS_CHOICES = [
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('AWAITING_CONFIRMATION', 'Awaiting NGO Confirmation'),
        ('COMPLETED', 'Completed'),
        ('DECLINED', 'Declined'),
    ]
    
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name='task')
    assigned_volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks_by')
    
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='TASK_ASSIGNED')
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"Task for {self.complaint.title} - {self.assigned_volunteer.username}"


class TaskCompletionProof(models.Model):
    """Store completion proof images for tasks"""
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='completion_proofs')
    image = models.ImageField(upload_to='task_proofs/')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Proof for Task #{self.task.id} - {self.uploaded_at.strftime('%Y-%m-%d')}"
