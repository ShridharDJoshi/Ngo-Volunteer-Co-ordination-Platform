from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from .models import Task, TaskCompletionProof
from .forms import TaskAssignmentForm, TaskCompletionProofForm
from complaints.models import Complaint, ComplaintStatusLog
from notifications.models import Notification


@login_required
def task_list(request):
    """List tasks based on user role"""
    if request.user.is_volunteer():
        tasks = Task.objects.filter(assigned_volunteer=request.user)
    elif request.user.is_ngo():
        tasks = Task.objects.filter(
            models.Q(assigned_by=request.user) |
            models.Q(complaint__linked_ngo__user=request.user) |
            models.Q(complaint__assigned_ngo__user=request.user)
        ).distinct()
    elif request.user.is_admin_user():
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.none()
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    tasks = tasks.select_related('complaint', 'assigned_volunteer').order_by('-assigned_at')
    
    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'status_filter': status_filter
    })


@login_required
def task_detail(request, task_id):
    """View task details"""
    task = get_object_or_404(Task, id=task_id)
    
    # Permission check
    can_view = False
    if request.user.is_admin_user():
        can_view = True
    elif task.assigned_volunteer == request.user:
        can_view = True
    elif request.user.is_ngo() and (
        task.assigned_by == request.user or
        (task.complaint.linked_ngo and task.complaint.linked_ngo.user == request.user) or
        (task.complaint.assigned_ngo and task.complaint.assigned_ngo.user == request.user)
    ):
        can_view = True
    
    if not can_view:
        messages.error(request, 'You do not have permission to view this task.')
        return redirect('tasks:task_list')
    
    # Get completion proofs
    proofs = task.completion_proofs.all()
    
    context = {
        'task': task,
        'proofs': proofs,
    }
    
    return render(request, 'tasks/task_detail.html', context)


@login_required
def assign_task(request, complaint_id):
    """NGO assigns a task to a volunteer"""
    if not request.user.is_ngo():
        messages.error(request, 'Only NGOs can assign tasks.')
        return redirect('users:dashboard')
    
    complaint = get_object_or_404(Complaint, id=complaint_id, linked_ngo__user=request.user)
    
    # Check if complaint is accepted
    if complaint.status != 'ACCEPTED':
        messages.error(request, 'Can only assign tasks to accepted complaints.')
        return redirect('complaints:complaint_detail', complaint_id=complaint.id)
    
    # Check if task already exists
    if hasattr(complaint, 'task'):
        messages.warning(request, 'A task has already been assigned for this complaint.')
        return redirect('tasks:task_detail', task_id=complaint.task.id)
    
    if request.method == 'POST':
        form = TaskAssignmentForm(ngo_profile=request.user.ngo_profile, data=request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.complaint = complaint
            task.assigned_by = request.user
            task.save()
            
            # Update complaint status
            old_status = complaint.status
            complaint.status = 'TASK_ASSIGNED'
            complaint.save()
            
            # Create status log
            ComplaintStatusLog.objects.create(
                complaint=complaint,
                old_status=old_status,
                new_status='TASK_ASSIGNED',
                changed_by=request.user,
                note=f'Task assigned to {task.assigned_volunteer.username}'
            )
            
            # Create notification for volunteer
            Notification.create_notification(
                recipient=task.assigned_volunteer,
                sender=request.user,
                notification_type='TASK_ASSIGNED',
                message=f'You have been assigned a task for complaint: "{complaint.title}"',
                related_object_id=task.id,
                related_object_type='task'
            )
            
            messages.success(request, f'Task assigned to {task.assigned_volunteer.username}!')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskAssignmentForm(ngo_profile=request.user.ngo_profile)
    
    return render(request, 'tasks/assign_task.html', {
        'form': form,
        'complaint': complaint
    })


@login_required
def accept_task(request, task_id):
    """Volunteer accepts a task"""
    if not request.user.is_volunteer():
        messages.error(request, 'Only volunteers can accept tasks.')
        return redirect('users:dashboard')
    
    task = get_object_or_404(Task, id=task_id, assigned_volunteer=request.user)
    
    if task.status != 'TASK_ASSIGNED':
        messages.warning(request, 'This task has already been processed.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    task.status = 'IN_PROGRESS'
    task.accepted_at = timezone.now()
    task.save()
    
    # Update complaint status
    old_status = task.complaint.status
    task.complaint.status = 'IN_PROGRESS'
    task.complaint.save()
    
    # Create status log
    ComplaintStatusLog.objects.create(
        complaint=task.complaint,
        old_status=old_status,
        new_status='IN_PROGRESS',
        changed_by=request.user,
        note=f'Task accepted by volunteer {request.user.username}. Work is now in progress.'
    )
    
    # Create notification for NGO
    Notification.create_notification(
        recipient=task.assigned_by,
        sender=request.user,
        notification_type='TASK_ACCEPTED',
        message=f'{request.user.username} has accepted the task for "{task.complaint.title}"',
        related_object_id=task.id,
        related_object_type='task'
    )
    
    messages.success(request, 'Task accepted! You can now start working on it.')
    return redirect('tasks:task_detail', task_id=task.id)


@login_required
def decline_task(request, task_id):
    """Volunteer declines a task"""
    if not request.user.is_volunteer():
        messages.error(request, 'Only volunteers can decline tasks.')
        return redirect('users:dashboard')
    
    task = get_object_or_404(Task, id=task_id, assigned_volunteer=request.user)
    
    if task.status != 'TASK_ASSIGNED':
        messages.warning(request, 'This task has already been processed.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    task.status = 'DECLINED'
    task.save()
    
    # Update complaint status back to ACCEPTED
    old_status = task.complaint.status
    task.complaint.status = 'ACCEPTED'
    task.complaint.save()
    
    # Create status log
    ComplaintStatusLog.objects.create(
        complaint=task.complaint,
        old_status=old_status,
        new_status='ACCEPTED',
        changed_by=request.user,
        note=f'Task declined by volunteer {request.user.username}. Complaint returned to ACCEPTED status - ready for reassignment to another volunteer.'
    )
    
    # Create notification for NGO
    Notification.create_notification(
        recipient=task.assigned_by,
        sender=request.user,
        notification_type='TASK_DECLINED',
        message=f'{request.user.username} has declined the task for "{task.complaint.title}"',
        related_object_id=task.id,
        related_object_type='task'
    )
    
    messages.info(request, 'Task declined.')
    return redirect('tasks:task_list')


@login_required
def upload_proof(request, task_id):
    """Volunteer uploads completion proof"""
    if not request.user.is_volunteer():
        messages.error(request, 'Only volunteers can upload proof.')
        return redirect('users:dashboard')
    
    task = get_object_or_404(Task, id=task_id, assigned_volunteer=request.user)
    
    if task.status not in ['IN_PROGRESS', 'AWAITING_CONFIRMATION']:
        messages.warning(request, 'Cannot upload proof for this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        form = TaskCompletionProofForm(request.POST, request.FILES)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.task = task
            proof.save()
            
            messages.success(request, 'Proof uploaded successfully!')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskCompletionProofForm()
    
    return render(request, 'tasks/upload_proof.html', {
        'form': form,
        'task': task
    })


@login_required
def mark_complete(request, task_id):
    """Volunteer marks task as complete"""
    if not request.user.is_volunteer():
        messages.error(request, 'Only volunteers can mark tasks complete.')
        return redirect('users:dashboard')
    
    task = get_object_or_404(Task, id=task_id, assigned_volunteer=request.user)
    
    if task.status != 'IN_PROGRESS':
        messages.warning(request, 'Cannot mark this task as complete.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    # Check if at least one proof image exists
    if not task.completion_proofs.exists():
        messages.error(request, 'Please upload at least one completion proof image before marking as complete.')
        return redirect('tasks:upload_proof', task_id=task.id)
    
    task.status = 'AWAITING_CONFIRMATION'
    task.save()
    
    # Create status log for tracking
    ComplaintStatusLog.objects.create(
        complaint=task.complaint,
        old_status=task.complaint.status,
        new_status=task.complaint.status,
        changed_by=request.user,
        note=f'Task marked as complete by volunteer. Awaiting NGO confirmation of completion proof.'
    )
    
    # Create notification for NGO
    Notification.create_notification(
        recipient=task.assigned_by,
        sender=request.user,
        notification_type='TASK_COMPLETED',
        message=f'{request.user.username} has completed the task for "{task.complaint.title}". Please review and confirm.',
        related_object_id=task.id,
        related_object_type='task'
    )
    
    messages.success(request, 'Task marked as complete! Waiting for NGO confirmation.')
    return redirect('tasks:task_detail', task_id=task.id)


@login_required
def confirm_completion(request, task_id):
    """NGO confirms task completion"""
    if not request.user.is_ngo():
        messages.error(request, 'Only NGOs can confirm completion.')
        return redirect('users:dashboard')
    
    task = get_object_or_404(
        Task.objects.filter(
            models.Q(assigned_by=request.user) |
            models.Q(complaint__linked_ngo__user=request.user) |
            models.Q(complaint__assigned_ngo__user=request.user)
        ).distinct(),
        id=task_id
    )
    
    if task.status != 'AWAITING_CONFIRMATION':
        messages.warning(request, 'This task is not awaiting confirmation.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    task.status = 'COMPLETED'
    task.completed_at = timezone.now()
    task.save()
    
    # Update complaint status
    old_status = task.complaint.status
    task.complaint.status = 'COMPLETED'
    task.complaint.save()
    
    # Create status log
    ComplaintStatusLog.objects.create(
        complaint=task.complaint,
        old_status=old_status,
        new_status='COMPLETED',
        changed_by=request.user,
        note='Task completion confirmed by NGO'
    )
    
    # Create notification for volunteer
    Notification.create_notification(
        recipient=task.assigned_volunteer,
        sender=request.user,
        notification_type='COMPLETION_CONFIRMED',
        message=f'Your work on "{task.complaint.title}" has been confirmed as complete!',
        related_object_id=task.id,
        related_object_type='task'
    )
    
    # Create notification for complaint submitter
    Notification.create_notification(
        recipient=task.complaint.submitted_by,
        sender=request.user,
        notification_type='COMPLAINT_RESOLVED',
        message=f'Your complaint "{task.complaint.title}" has been resolved! Thank you for reporting this issue.',
        related_object_id=task.complaint.id,
        related_object_type='complaint'
    )
    
    messages.success(request, 'Task completion confirmed!')
    return redirect('tasks:task_detail', task_id=task.id)


@login_required
def reject_proof(request, task_id):
    """NGO rejects task completion proof"""
    if not request.user.is_ngo():
        messages.error(request, 'Only NGOs can reject proof.')
        return redirect('users:dashboard')
    
    task = get_object_or_404(
        Task.objects.filter(
            models.Q(assigned_by=request.user) |
            models.Q(complaint__linked_ngo__user=request.user) |
            models.Q(complaint__assigned_ngo__user=request.user)
        ).distinct(),
        id=task_id
    )
    
    if task.status != 'AWAITING_CONFIRMATION':
        messages.warning(request, 'This task is not awaiting confirmation.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    task.status = 'IN_PROGRESS'
    task.accepted_at = timezone.now()
    task.save()
    
    # Update complaint status
    old_status = task.complaint.status
    task.complaint.status = 'IN_PROGRESS'
    task.complaint.save()
    
    # Create status log
    ComplaintStatusLog.objects.create(
        complaint=task.complaint,
        old_status=old_status,
        new_status='IN_PROGRESS',
        changed_by=request.user,
        note='Completion proof rejected by NGO. Task moved back to in progress for revision.'
    )
    
    # Create notification for volunteer
    Notification.create_notification(
        recipient=task.assigned_volunteer,
        sender=request.user,
        notification_type='PROOF_REJECTED',
        message=f'The completion proof for "{task.complaint.title}" needs revision. Please update and resubmit.',
        related_object_id=task.id,
        related_object_type='task'
    )
    
    messages.info(request, 'Proof rejected. Volunteer has been notified.')
    return redirect('tasks:task_detail', task_id=task.id)
