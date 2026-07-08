from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import NGOProfile, Membership
from notifications.models import Notification


@login_required
def ngo_list(request):
    """List all NGOs for volunteers to join"""
    if not request.user.is_volunteer():
        messages.error(request, 'Only volunteers can view this page.')
        return redirect('users:dashboard')
    
    # Show only verified NGOs
    ngos = NGOProfile.objects.filter(is_verified=True).order_by('organization_name')
    
    # Get user's existing memberships
    user_memberships = Membership.objects.filter(volunteer=request.user).values_list('ngo_id', 'status')
    membership_dict = dict(user_memberships)
    
    # Add membership status to each NGO
    for ngo in ngos:
        ngo.membership_status = membership_dict.get(ngo.id)
    
    return render(request, 'ngos/ngo_list.html', {'ngos': ngos})


@login_required
def ngo_detail(request, ngo_id):
    """View NGO details"""
    ngo = get_object_or_404(NGOProfile, id=ngo_id)
    
    # Check if volunteer has membership
    membership = None
    if request.user.is_volunteer():
        try:
            membership = Membership.objects.get(volunteer=request.user, ngo=ngo)
        except Membership.DoesNotExist:
            pass
    
    # Get approved volunteers (public info)
    approved_volunteers = Membership.objects.filter(ngo=ngo, status='APPROVED').select_related('volunteer')
    
    context = {
        'ngo': ngo,
        'membership': membership,
        'approved_volunteers': approved_volunteers,
    }
    
    return render(request, 'ngos/ngo_detail.html', context)


@login_required
def request_membership(request, ngo_id):
    """Volunteer requests to join an NGO"""
    if not request.user.is_volunteer():
        messages.error(request, 'Only volunteers can request membership.')
        return redirect('users:dashboard')
    
    ngo = get_object_or_404(NGOProfile, id=ngo_id)
    
    # Check for existing membership
    existing = Membership.objects.filter(volunteer=request.user, ngo=ngo).first()
    
    if existing:
        if existing.status == 'PENDING':
            messages.warning(request, 'You already have a pending request with this NGO.')
        elif existing.status == 'APPROVED':
            messages.info(request, 'You are already a member of this NGO.')
        elif existing.status == 'REJECTED':
            # Allow re-requesting after rejection
            existing.status = 'PENDING'
            existing.updated_at = timezone.now()
            existing.save()
            messages.success(request, 'Membership request re-submitted successfully!')
            
            # Create notification for NGO
            Notification.create_notification(
                recipient=ngo.user,
                sender=request.user,
                notification_type='MEMBERSHIP_REQUEST',
                message=f'{request.user.username} has requested to join {ngo.organization_name}.',
                related_object_id=existing.id,
                related_object_type='membership'
            )
        return redirect('ngos:ngo_detail', ngo_id=ngo.id)
    
    # Create new membership request
    membership = Membership.objects.create(
        volunteer=request.user,
        ngo=ngo,
        status='PENDING'
    )
    
    # Create notification for NGO
    Notification.create_notification(
        recipient=ngo.user,
        sender=request.user,
        notification_type='MEMBERSHIP_REQUEST',
        message=f'{request.user.username} has requested to join {ngo.organization_name}.',
        related_object_id=membership.id,
        related_object_type='membership'
    )
    
    messages.success(request, f'Membership request sent to {ngo.organization_name}!')
    return redirect('ngos:ngo_detail', ngo_id=ngo.id)


@login_required
def approve_membership(request, membership_id):
    """NGO approves a membership request"""
    if not request.user.is_ngo():
        messages.error(request, 'Only NGOs can approve memberships.')
        return redirect('users:dashboard')
    
    membership = get_object_or_404(Membership, id=membership_id, ngo__user=request.user)
    
    if membership.status != 'PENDING':
        messages.warning(request, 'This request has already been processed.')
        return redirect('users:dashboard')
    
    membership.status = 'APPROVED'
    membership.save()
    
    # Create notification for volunteer
    Notification.create_notification(
        recipient=membership.volunteer,
        sender=request.user,
        notification_type='MEMBERSHIP_APPROVED',
        message=f'Your membership request to {membership.ngo.organization_name} has been approved!',
        related_object_id=membership.id,
        related_object_type='membership'
    )
    
    messages.success(request, f'Approved {membership.volunteer.username} as a member!')
    return redirect('users:dashboard')


@login_required
def reject_membership(request, membership_id):
    """NGO rejects a membership request"""
    if not request.user.is_ngo():
        messages.error(request, 'Only NGOs can reject memberships.')
        return redirect('users:dashboard')
    
    membership = get_object_or_404(Membership, id=membership_id, ngo__user=request.user)
    
    if membership.status != 'PENDING':
        messages.warning(request, 'This request has already been processed.')
        return redirect('users:dashboard')
    
    membership.status = 'REJECTED'
    membership.save()
    
    # Create notification for volunteer
    Notification.create_notification(
        recipient=membership.volunteer,
        sender=request.user,
        notification_type='MEMBERSHIP_REJECTED',
        message=f'Your membership request to {membership.ngo.organization_name} has been rejected.',
        related_object_id=membership.id,
        related_object_type='membership'
    )
    
    messages.info(request, f'Rejected membership request from {membership.volunteer.username}.')
    return redirect('users:dashboard')


@login_required
def leave_ngo(request, membership_id):
    """Volunteer leaves an NGO"""
    if not request.user.is_volunteer():
        messages.error(request, 'Only volunteers can leave NGOs.')
        return redirect('users:dashboard')
    
    membership = get_object_or_404(Membership, id=membership_id, volunteer=request.user)
    
    if membership.status != 'APPROVED':
        messages.warning(request, 'You are not a member of this NGO.')
        return redirect('users:dashboard')
    
    membership.status = 'REMOVED'
    membership.save()
    
    messages.success(request, f'You have left {membership.ngo.organization_name}.')
    return redirect('users:dashboard')


@login_required
def my_memberships(request):
    """View volunteer's memberships"""
    if not request.user.is_volunteer():
        messages.error(request, 'Only volunteers can view memberships.')
        return redirect('users:dashboard')
    
    memberships = Membership.objects.filter(volunteer=request.user).select_related('ngo').order_by('-created_at')
    
    return render(request, 'ngos/my_memberships.html', {'memberships': memberships})
