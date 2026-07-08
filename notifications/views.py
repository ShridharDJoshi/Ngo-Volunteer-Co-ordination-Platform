from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list(request):
    """View all notifications"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications.update(is_read=True)
        return redirect('notifications:notification_list')
    
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def mark_as_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    return redirect('notifications:notification_list')


@login_required
def mark_as_unread(request, notification_id):
    """Mark a notification as unread"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = False
    notification.save()
    
    return redirect('notifications:notification_list')


@login_required
def delete_notification(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.delete()
    
    return redirect('notifications:notification_list')


@login_required
def unread_count(request):
    """API endpoint for unread notification count"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})
