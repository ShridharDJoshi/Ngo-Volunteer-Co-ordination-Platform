from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Notification system for tracking all user interactions"""
    
    NOTIFICATION_TYPES = [
        ('MEMBERSHIP_REQUEST', 'Membership Request'),
        ('MEMBERSHIP_APPROVED', 'Membership Approved'),
        ('MEMBERSHIP_REJECTED', 'Membership Rejected'),
        ('COMPLAINT_ACCEPTED', 'Complaint Accepted'),
        ('COMPLAINT_REJECTED', 'Complaint Rejected'),
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('TASK_ACCEPTED', 'Task Accepted'),
        ('TASK_DECLINED', 'Task Declined'),
        ('TASK_COMPLETED', 'Task Completed'),
        ('COMPLETION_CONFIRMED', 'Completion Confirmed'),
        ('PROOF_REJECTED', 'Proof Rejected'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    
    notification_type = models.CharField(max_length=25, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    
    # Generic relationship fields
    related_object_id = models.IntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)  # e.g., 'complaint', 'task', 'membership'
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient.username}"
    
    @staticmethod
    def create_notification(recipient, sender, notification_type, message, related_object_id=None, related_object_type=None):
        """Helper method to create notifications"""
        return Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            message=message,
            related_object_id=related_object_id,
            related_object_type=related_object_type
        )
