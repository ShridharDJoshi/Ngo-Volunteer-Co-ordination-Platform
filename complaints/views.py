from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from .models import Complaint, ComplaintStatusLog, ComplaintHelpRequest
from .forms import ComplaintForm, HelpRequestForm
from ngos.models import Membership
from notifications.models import Notification
from tasks.models import Task


@login_required
def complaint_list(request):
    """List all complaints (role-based filtering with new visibility rules)"""
    if request.user.is_volunteer():
        # Volunteers see:
        # 1. Their own complaints
        # 2. Complaints they are helping with
        # 3. Complaints where they have pending/processed help requests
        complaints = Complaint.objects.filter(
            models.Q(submitted_by=request.user) | 
            models.Q(volunteers_helping=request.user) |
            models.Q(help_requests__volunteer=request.user)
        ).distinct()
        
    elif request.user.is_ngo():
        # NGOs see:
        # 1. Public complaints (no linked_ngo and not assigned)
        # 2. Complaints linked to them
        # 3. Complaints they are assigned to handle
        complaints = Complaint.objects.filter(
            models.Q(linked_ngo__user=request.user) |
            models.Q(assigned_ngo__user=request.user) |
            models.Q(linked_ngo__isnull=True, is_assigned=False)
        ).distinct()
        
    elif request.user.is_admin_user():
        # Admins see all complaints
        complaints = Complaint.objects.all()
    else:
        complaints = Complaint.objects.none()
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    
    complaints = complaints.order_by('-created_at')
    
    return render(request, 'complaints/complaint_list.html', {
        'complaints': complaints,
        'status_filter': status_filter
    })


@login_required
def complaint_detail(request, complaint_id):
    """View complaint details"""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Permission check with new visibility rules
    can_view = False
    if request.user.is_admin_user():
        can_view = True
    elif complaint.submitted_by == request.user:
        can_view = True
    elif request.user.is_ngo():
        # NGO can view if: linked to them, assigned to them, or public and not assigned
        if complaint.linked_ngo and complaint.linked_ngo.user == request.user:
            can_view = True
        elif complaint.assigned_ngo and complaint.assigned_ngo.user == request.user:
            can_view = True
        elif not complaint.linked_ngo and not complaint.is_assigned:
            can_view = True
    elif request.user in complaint.volunteers_helping.all():
        # Volunteer helping with this complaint
        can_view = True
    elif request.user.is_volunteer() and complaint.help_requests.filter(volunteer=request.user).exists():
        # Volunteer can view complaint if NGO has requested their help
        can_view = True
    
    if not can_view:
        messages.error(request, 'You do not have permission to view this complaint.')
        return redirect('complaints:complaint_list')
    
    # Get status logs
    status_logs = complaint.status_logs.all()
    
    # Check if there's a task
    task = None
    if hasattr(complaint, 'task'):
        task = complaint.task
    
    # Get help requests for this complaint
    help_requests = complaint.help_requests.all()
    
    # Check if current user is NGO and can request help
    can_request_help = request.user.is_ngo() and (
        (complaint.linked_ngo and complaint.linked_ngo.user == request.user) or
        (not complaint.linked_ngo and not complaint.is_assigned)
    )
    
    context = {
        'complaint': complaint,
        'status_logs': status_logs,
        'task': task,
        'help_requests': help_requests,
        'can_request_help': can_request_help,
    }
    
    return render(request, 'complaints/complaint_detail.html', context)


@login_required
def complaint_create(request):
    """Create a new complaint - available to all authenticated users"""
    
    if request.method == 'POST':
        form = ComplaintForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.submitted_by = request.user
            complaint.save()
            
            # Create status log
            ComplaintStatusLog.objects.create(
                complaint=complaint,
                new_status='PENDING',
                changed_by=request.user,
                note='Complaint submitted'
            )
            
            # If linked to specific NGO, notify them
            if complaint.linked_ngo:
                Notification.create_notification(
                    recipient=complaint.linked_ngo.user,
                    sender=request.user,
                    notification_type='COMPLAINT_ACCEPTED',
                    message=f'New complaint "{complaint.title}" has been submitted by {request.user.username}.',
                    related_object_id=complaint.id,
                    related_object_type='complaint'
                )
            else:
                # Public complaint - notify all NGOs
                from ngos.models import NGOProfile
                all_ngos = NGOProfile.objects.all()
                for ngo_profile in all_ngos:
                    Notification.create_notification(
                        recipient=ngo_profile.user,
                        sender=request.user,
                        notification_type='COMPLAINT_ACCEPTED',
                        message=f'New public complaint "{complaint.title}" is available at {complaint.location}.',
                        related_object_id=complaint.id,
                        related_object_type='complaint'
                    )
            
            messages.success(request, 'Complaint submitted successfully! NGOs have been notified.')
            return redirect('complaints:complaint_detail', complaint_id=complaint.id)
    else:
        form = ComplaintForm(user=request.user)
    
    return render(request, 'complaints/complaint_form.html', {'form': form})


@login_required
def accept_complaint(request, complaint_id):
    """NGO accepts a complaint"""
    if not request.user.is_ngo():
        messages.error(request, 'Only NGOs can accept complaints.')
        return redirect('users:dashboard')
    
    complaint = get_object_or_404(Complaint, id=complaint_id, linked_ngo__user=request.user)
    
    if complaint.status != 'PENDING':
        messages.warning(request, 'This complaint has already been processed.')
        return redirect('complaints:complaint_detail', complaint_id=complaint.id)
    
    old_status = complaint.status
    complaint.status = 'ACCEPTED'
    complaint.save()
    
    # Create status log
    ComplaintStatusLog.objects.create(
        complaint=complaint,
        old_status=old_status,
        new_status='ACCEPTED',
        changed_by=request.user,
        note='Complaint accepted by NGO'
    )
    
    # Create notification for volunteer
    Notification.create_notification(
        recipient=complaint.submitted_by,
        sender=request.user,
        notification_type='COMPLAINT_ACCEPTED',
        message=f'Your complaint "{complaint.title}" has been accepted by {request.user.ngo_profile.organization_name}.',
        related_object_id=complaint.id,
        related_object_type='complaint'
    )
    
    messages.success(request, 'Complaint accepted successfully!')
    return redirect('complaints:complaint_detail', complaint_id=complaint.id)


@login_required
def reject_complaint(request, complaint_id):
    """NGO rejects a complaint"""
    if not request.user.is_ngo():
        messages.error(request, 'Only NGOs can reject complaints.')
        return redirect('users:dashboard')
    
    complaint = get_object_or_404(Complaint, id=complaint_id, linked_ngo__user=request.user)
    
    if complaint.status != 'PENDING':
        messages.warning(request, 'This complaint has already been processed.')
        return redirect('complaints:complaint_detail', complaint_id=complaint.id)
    
    old_status = complaint.status
    complaint.status = 'REJECTED'
    complaint.save()
    
    # Create status log
    ComplaintStatusLog.objects.create(
        complaint=complaint,
        old_status=old_status,
        new_status='REJECTED',
        changed_by=request.user,
        note='Complaint rejected by NGO'
    )
    
    # Create notification for volunteer
    Notification.create_notification(
        recipient=complaint.submitted_by,
        sender=request.user,
        notification_type='COMPLAINT_REJECTED',
        message=f'Your complaint "{complaint.title}" has been rejected by {request.user.ngo_profile.organization_name}.',
        related_object_id=complaint.id,
        related_object_type='complaint'
    )
    
    messages.info(request, 'Complaint rejected.')
    return redirect('complaints:complaint_detail', complaint_id=complaint.id)


@login_required
def request_volunteer_help(request, complaint_id):
    """NGO requests volunteer help for a complaint"""
    if not request.user.is_ngo():
        messages.error(request, 'Only NGOs can request volunteer help.')
        return redirect('users:dashboard')
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Check if NGO can request help for this complaint
    can_request = False
    if complaint.linked_ngo and complaint.linked_ngo.user == request.user:
        can_request = True
    elif not complaint.linked_ngo and not complaint.is_assigned:
        can_request = True
    
    if not can_request:
        messages.error(request, 'You cannot request help for this complaint.')
        return redirect('complaints:complaint_detail', complaint_id=complaint.id)
    
    if complaint.is_assigned:
        messages.warning(request, 'This complaint has already been assigned.')
        return redirect('complaints:complaint_detail', complaint_id=complaint.id)
    
    if request.method == 'POST':
        form = HelpRequestForm(ngo_user=request.user, data=request.POST)
        if form.is_valid():
            help_request = form.save(commit=False)
            help_request.complaint = complaint
            help_request.ngo = request.user.ngo_profile
            help_request.save()
            
            # Create notification for volunteer
            Notification.create_notification(
                recipient=help_request.volunteer,
                sender=request.user,
                notification_type='COMPLAINT_ACCEPTED',
                message=f'{request.user.ngo_profile.organization_name} is requesting your help with complaint "{complaint.title}".',
                related_object_id=complaint.id,
                related_object_type='complaint'
            )
            
            messages.success(request, f'Help request sent to {help_request.volunteer.username}!')
            return redirect('complaints:complaint_detail', complaint_id=complaint.id)
    else:
        form = HelpRequestForm(ngo_user=request.user)
    
    return render(request, 'complaints/request_help_form.html', {
        'form': form,
        'complaint': complaint
    })


@login_required
def accept_help_request(request, request_id):
    """Volunteer accepts a help request"""
    if not request.user.is_volunteer():
        messages.error(request, 'Only volunteers can accept help requests.')
        return redirect('users:dashboard')
    
    help_request = get_object_or_404(ComplaintHelpRequest, id=request_id, volunteer=request.user)
    
    if help_request.status != 'PENDING':
        messages.warning(request, 'This help request has already been processed.')
        return redirect('complaints:complaint_detail', complaint_id=help_request.complaint.id)
    
    # Update help request
    help_request.status = 'ACCEPTED'
    help_request.responded_at = timezone.now()
    help_request.save()
    
    # Update complaint
    complaint = help_request.complaint
    if not complaint.is_assigned:
        complaint.is_assigned = True
        complaint.assigned_ngo = help_request.ngo
    complaint.volunteers_helping.add(request.user)
    old_status = complaint.status
    complaint.status = 'IN_PROGRESS'
    complaint.save()

    # Create or sync task so volunteer can upload proof and mark complete
    task, created = Task.objects.get_or_create(
        complaint=complaint,
        defaults={
            'assigned_volunteer': request.user,
            'assigned_by': help_request.ngo.user,
            'status': 'IN_PROGRESS',
            'accepted_at': timezone.now(),
        },
    )

    if not created:
        # If task already exists for same volunteer, move it to in-progress.
        if task.assigned_volunteer == request.user:
            task.status = 'IN_PROGRESS'
            if not task.accepted_at:
                task.accepted_at = timezone.now()
            task.save()

    ComplaintStatusLog.objects.create(
        complaint=complaint,
        old_status=old_status,
        new_status='IN_PROGRESS',
        changed_by=request.user,
        note=f'Help accepted by volunteer {request.user.username}. Task is now in progress.'
    )
    
    # Create notification for NGO
    Notification.create_notification(
        recipient=help_request.ngo.user,
        sender=request.user,
        notification_type='COMPLAINT_ACCEPTED',
        message=f'{request.user.username} has accepted your help request for complaint "{complaint.title}".',
        related_object_id=complaint.id,
        related_object_type='complaint'
    )
    
    # Notify complaint submitter
    if complaint.submitted_by != request.user:
        Notification.create_notification(
            recipient=complaint.submitted_by,
            sender=request.user,
            notification_type='COMPLAINT_ACCEPTED',
            message=f'Volunteer {request.user.username} is now helping with your complaint "{complaint.title}".',
            related_object_id=complaint.id,
            related_object_type='complaint'
        )

    # Create task notification for volunteer to continue proof flow
    Notification.create_notification(
        recipient=request.user,
        sender=help_request.ngo.user,
        notification_type='TASK_ASSIGNED',
        message=f'Task started for "{complaint.title}". Upload proof and mark as complete when done.',
        related_object_id=task.id,
        related_object_type='task'
    )
    
    messages.success(request, 'Help request accepted. Task is now in progress. Upload proof and mark complete after work is done.')
    return redirect('tasks:task_detail', task_id=task.id)


@login_required
def decline_help_request(request, request_id):
    """Volunteer declines a help request"""
    if not request.user.is_volunteer():
        messages.error(request, 'Only volunteers can decline help requests.')
        return redirect('users:dashboard')
    
    help_request = get_object_or_404(ComplaintHelpRequest, id=request_id, volunteer=request.user)
    
    if help_request.status != 'PENDING':
        messages.warning(request, 'This help request has already been processed.')
        return redirect('complaints:complaint_detail', complaint_id=help_request.complaint.id)
    
    # Update help request
    help_request.status = 'DECLINED'
    help_request.responded_at = timezone.now()
    help_request.save()
    
    # Create notification for NGO
    Notification.create_notification(
        recipient=help_request.ngo.user,
        sender=request.user,
        notification_type='COMPLAINT_REJECTED',
        message=f'{request.user.username} has declined your help request for complaint "{help_request.complaint.title}".',
        related_object_id=help_request.complaint.id,
        related_object_type='complaint'
    )
    
    messages.info(request, 'You have declined the help request.')
    return redirect('complaints:complaint_list')
