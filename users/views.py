from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .forms import CustomUserRegistrationForm, VolunteerProfileForm, NGOProfileForm
from .models import CustomUser
from ngos.models import VolunteerProfile, NGOProfile, Membership
from complaints.models import Complaint, ComplaintHelpRequest
from tasks.models import Task
from notifications.models import Notification


def home_view(request):
    """Landing page view"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    return render(request, 'home.html')


def login_choice_view(request):
    """Login role selection page"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    return render(request, 'users/login_choice.html')


def register_choice_view(request):
    """Registration role selection page"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    return render(request, 'users/register_choice.html')


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    
    # Get role from URL parameter
    role = request.GET.get('role', '').lower()
    
    # Redirect to choice page if no role is specified
    if not role or role not in ['volunteer', 'ngo']:
        messages.info(request, 'Please select your registration type.')
        return redirect('users:register_choice')
    
    if request.method == 'POST':
        # Get role from POST data (hidden field)
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Registration successful! Welcome to Community Sanitation Platform as a {role.capitalize()}.')
            return redirect('users:dashboard')
    else:
        # Pre-fill role based on URL parameter
        initial_data = {'role': role.upper()}
        form = CustomUserRegistrationForm(initial=initial_data)
    
    context = {
        'form': form,
        'selected_role': role.capitalize(),
        'role_value': role.upper()
    }
    return render(request, 'users/register.html', context)


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    
    # Get role from URL parameter for display purposes
    role = request.GET.get('role', '').lower()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verify role matches if specified
            if role and role != 'admin':
                expected_role = role.upper()
                if user.role != expected_role:
                    messages.error(request, f'This account is not registered as a {role.capitalize()}.')
                    return render(request, 'users/login.html', {'selected_role': role.capitalize()})
            elif role == 'admin':
                if not user.is_admin_user():
                    messages.error(request, 'This account does not have administrator privileges.')
                    return render(request, 'users/login.html', {'selected_role': 'Administrator'})
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'users:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    context = {
        'selected_role': role.capitalize() if role and role != 'admin' else ('Administrator' if role == 'admin' else None)
    }
    return render(request, 'users/login.html', context)


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard_view(request):
    """Main dashboard - routes to appropriate dashboard based on role"""
    # Check admin first (includes superusers)
    if request.user.is_admin_user():
        return admin_dashboard(request)
    elif request.user.is_volunteer():
        return volunteer_dashboard(request)
    elif request.user.is_ngo():
        return ngo_dashboard(request)
    else:
        messages.error(request, 'Invalid user role. Please contact administrator.')
        logout(request)
        return redirect('home')


@login_required
def volunteer_dashboard(request):
    """Volunteer dashboard with complaints, tasks, and memberships"""
    # Verify user is actually a volunteer
    if not request.user.is_volunteer():
        messages.error(request, 'Access denied. You are not registered as a volunteer.')
        return redirect('users:dashboard')
    
    try:
        profile = request.user.volunteer_profile
    except VolunteerProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = VolunteerProfile.objects.create(user=request.user)
    
    # Get volunteer's data
    my_complaints = Complaint.objects.filter(submitted_by=request.user).order_by('-created_at')
    my_tasks = Task.objects.filter(assigned_volunteer=request.user).order_by('-assigned_at')
    my_memberships = Membership.objects.filter(volunteer=request.user, status='APPROVED')
    pending_requests = Membership.objects.filter(volunteer=request.user, status='PENDING')
    pending_help_requests = ComplaintHelpRequest.objects.filter(
        volunteer=request.user,
        status='PENDING'
    ).select_related('complaint', 'ngo').order_by('-created_at')
    
    # Statistics
    total_complaints = my_complaints.count()
    completed_tasks = my_tasks.filter(status='COMPLETED').count()
    in_progress_tasks = my_tasks.filter(status='IN_PROGRESS').count()
    
    # Recent notifications
    recent_notifications = Notification.objects.filter(recipient=request.user)[:5]
    
    context = {
        'profile': profile,
        'my_complaints': my_complaints[:5],
        'my_tasks': my_tasks[:5],
        'my_memberships': my_memberships,
        'pending_requests': pending_requests,
        'pending_help_requests': pending_help_requests,
        'total_complaints': total_complaints,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'users/volunteer_dashboard.html', context)


@login_required
def ngo_dashboard(request):
    """NGO dashboard with complaints, tasks, and membership requests"""
    # Verify user is actually an NGO
    if not request.user.is_ngo():
        messages.error(request, 'Access denied. You are not registered as an NGO.')
        return redirect('users:dashboard')
    
    try:
        profile = request.user.ngo_profile
    except NGOProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = NGOProfile.objects.create(user=request.user, organization_name=request.user.username)
    
    # Check if NGO is verified
    if not profile.is_verified:
        messages.warning(request, 'Your NGO account is pending verification by an administrator. Please wait for approval before accessing the dashboard.')
        return render(request, 'users/ngo_pending_verification.html', {'profile': profile})
    
    # Get complaints visible to this NGO
    incoming_complaints = Complaint.objects.filter(
        Q(linked_ngo=profile) |
        Q(assigned_ngo=profile) |
        Q(linked_ngo__isnull=True, is_assigned=False)
    ).distinct().order_by('-created_at')
    pending_complaints = incoming_complaints.filter(status='PENDING')
    accepted_complaints = incoming_complaints.filter(status='ACCEPTED')
    
    # Membership requests
    membership_requests = Membership.objects.filter(ngo=profile, status='PENDING')
    approved_volunteers = Membership.objects.filter(ngo=profile, status='APPROVED')
    
    # Tasks
    active_tasks = Task.objects.filter(complaint__linked_ngo=profile, status__in=['TASK_ASSIGNED', 'IN_PROGRESS'])
    awaiting_confirmation = Task.objects.filter(complaint__linked_ngo=profile, status='AWAITING_CONFIRMATION')
    
    # Statistics
    total_complaints = incoming_complaints.count()
    completed_complaints = incoming_complaints.filter(status='COMPLETED').count()
    active_volunteers = approved_volunteers.count()
    
    # Recent notifications
    recent_notifications = Notification.objects.filter(recipient=request.user)[:5]
    
    context = {
        'profile': profile,
        'pending_complaints': pending_complaints[:5],
        'accepted_complaints': accepted_complaints[:5],
        'membership_requests': membership_requests[:5],
        'approved_volunteers': approved_volunteers[:10],
        'active_tasks': active_tasks[:5],
        'awaiting_confirmation': awaiting_confirmation[:5],
        'total_complaints': total_complaints,
        'completed_complaints': completed_complaints,
        'active_volunteers': active_volunteers,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'users/ngo_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard with system overview"""
    # Verify user is actually an admin
    if not request.user.is_admin_user():
        messages.error(request, 'Access denied. You do not have administrator privileges.')
        return redirect('users:dashboard')
    
    # System statistics
    total_users = CustomUser.objects.count()
    total_volunteers = CustomUser.objects.filter(role='VOLUNTEER').count()
    total_ngos = CustomUser.objects.filter(role='NGO').count()
    total_complaints = Complaint.objects.count()
    total_tasks = Task.objects.count()
    
    # Recent activity
    recent_users = CustomUser.objects.order_by('-created_at')[:10]
    recent_complaints = Complaint.objects.order_by('-created_at')[:10]
    recent_tasks = Task.objects.order_by('-assigned_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_volunteers': total_volunteers,
        'total_ngos': total_ngos,
        'total_complaints': total_complaints,
        'total_tasks': total_tasks,
        'recent_users': recent_users,
        'recent_complaints': recent_complaints,
        'recent_tasks': recent_tasks,
    }
    
    return render(request, 'users/admin_dashboard.html', context)


@login_required
def profile_view(request):
    """View user profile"""
    if request.user.is_volunteer():
        try:
            profile = request.user.volunteer_profile
        except VolunteerProfile.DoesNotExist:
            profile = VolunteerProfile.objects.create(user=request.user)
        template = 'users/volunteer_profile.html'
    elif request.user.is_ngo():
        try:
            profile = request.user.ngo_profile
        except NGOProfile.DoesNotExist:
            profile = NGOProfile.objects.create(user=request.user, organization_name=request.user.username)
        template = 'users/ngo_profile.html'
    elif request.user.is_admin_user():
        # Admins view basic user info
        context = {
            'user': request.user,
            'is_admin': True
        }
        return render(request, 'users/admin_profile.html', context)
    else:
        messages.error(request, 'Profile not found.')
        return redirect('users:dashboard')
    
    return render(request, template, {'profile': profile})


@login_required
def profile_edit(request):
    """Edit user profile"""
    if request.user.is_volunteer():
        try:
            profile = request.user.volunteer_profile
        except VolunteerProfile.DoesNotExist:
            profile = VolunteerProfile.objects.create(user=request.user)
        form_class = VolunteerProfileForm
        template = 'users/profile_edit.html'
    elif request.user.is_ngo():
        try:
            profile = request.user.ngo_profile
        except NGOProfile.DoesNotExist:
            profile = NGOProfile.objects.create(user=request.user, organization_name=request.user.username)
        form_class = NGOProfileForm
        template = 'users/profile_edit.html'
    elif request.user.is_admin_user():
        messages.info(request, 'Admin profiles cannot be edited through this interface.')
        return redirect('users:profile')
    else:
        messages.error(request, 'Cannot edit profile.')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = form_class(instance=profile)
    
    return render(request, template, {'form': form, 'profile': profile})
