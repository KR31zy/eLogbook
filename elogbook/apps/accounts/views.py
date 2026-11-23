from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import authenticate, login
from django.db.models import Count, Q
from django.urls import reverse
from datetime import timedelta
from django.http import HttpResponse
from .forms import UserSettingsForm
from elogbook.apps.assignments.models import AssignmentModal
import logging
from django.contrib.auth import logout
from django.http import HttpResponseForbidden

# FIXED: Import from the correct app
from elogbook.apps.logbook.models import LogbookTemplate, StudentLogbook, VirtualLogbook
from elogbook.apps.assignments.forms import AssignmentCreateForm
from .forms import AssignmentSubmissionForm

logger = logging.getLogger(__name__)

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            role = str(getattr(user, "role", "")).upper()
            print(f"LOGIN: {user.username}, Role: {role}, Has supervisor: {hasattr(user, 'supervisor_profile')}")
            
            if role == "SUPERVISOR" and hasattr(user, "supervisor_profile"):
                print("→ Redirecting to SUPERVISION dashboard")
                return redirect('supervision:dashboard')
            elif user.is_staff or user.is_superuser:
                print("→ Redirecting to ADMIN panel")
                return redirect('admin:index')  
            else:
                print("→ Redirecting to ACCOUNTS dashboard")
                return redirect('accounts:dashboard') 
            
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'accounts/login.html')

def home(request):
    return render(request, 'accounts/home.html')


@login_required
def dashboard(request):
    user = request.user  # Define user variable
    intern_obj = getattr(user, "intern_profile", None)
    internLoged = AssignmentModal.objects.filter(intern=intern_obj) if intern_obj else AssignmentModal.objects.none()

    # Add logbook data
    recent_logbooks = StudentLogbook.objects.filter(
        student=user
    ).select_related('template').order_by('-updated_at')[:5]
    
    # Calculate logbook statistics using virtual logbook
    total_weeks = 8  # Example: 8-week internship
    completed_logbooks = 0
    
    # Get virtual logbook progress if intern exists
    if intern_obj:
        try:
            virtual_logbook = VirtualLogbook.objects.get(intern=intern_obj)
            completed_logbooks = virtual_logbook.get_approved_weeks().count()
        except VirtualLogbook.DoesNotExist:
            completed_logbooks = 0
    
    in_progress_logbooks = StudentLogbook.objects.filter(
        student=user,
        status='draft'
    ).count()
    pending_logbooks = StudentLogbook.objects.filter(
        student=user,
        status='submitted'
    ).count()
    
    # Calculate logbook progress percentage
    logbook_progress = min(100, int((completed_logbooks / total_weeks) * 100)) if total_weeks > 0 else 0

    context = {
        "internloged": internLoged,
        'assignmentsSubmitForm': AssignmentCreateForm,
        "user": user,
        "current_date": timezone.now().strftime("%B %d, %Y"),
        "role_name": str(getattr(user, "role", "")).upper(),
        "days_remaining": 0,
        "supervisor": getattr(intern_obj, "supervisor", None) if intern_obj else None,
        "assignment_progress": 0,
        "log_progress": 0,
        "pending_approval": 0,
        "recent_assignments": [],
        "recent_activities": [],
        "pending_reviews_count": 0,
        
        # New logbook context variables
        "recent_logbooks": recent_logbooks,
        "logbook_progress": logbook_progress,
        "total_weeks": total_weeks,
        "completed_logbooks": completed_logbooks,
        "in_progress_logbooks": in_progress_logbooks,
        "pending_logbooks": pending_logbooks,
    }

    if intern_obj:
        today = timezone.now().date()
        
        if intern_obj.end_date:
            days_remaining = (intern_obj.end_date - today).days
            context["days_remaining"] = max(0, days_remaining)
            
            # Calculate weeks remaining based on virtual logbook uploads
            total_weeks = 8
            try:
                virtual_logbook = VirtualLogbook.objects.get(intern=intern_obj)
                uploaded_weeks = virtual_logbook.get_approved_weeks().count()
                weeks_remaining = max(0, total_weeks - uploaded_weeks)
            except VirtualLogbook.DoesNotExist:
                weeks_remaining = total_weeks
            context["weeks_remaining"] = weeks_remaining  

        try:
            from elogbook.apps.assignments.models import Assignment  
            total_assignments = Assignment.objects.filter(intern=intern_obj).count()
            completed_assignments = Assignment.objects.filter(
                intern=intern_obj, 
                status='approved'
            ).count()
            submitted_assignments = Assignment.objects.filter(
                intern=intern_obj, 
                status__in=['submitted', 'approved']
            ).count()
            
            if total_assignments > 0:
                context["assignment_progress"] = int((completed_assignments / total_assignments) * 100)
            else:
                context["assignment_progress"] = 0
                
            # Add assignment counts for the new display
            context["completed_assignments_count"] = submitted_assignments
            context["total_assignments_count"] = total_assignments
            
            context["recent_assignments"] = Assignment.objects.filter(
                intern=intern_obj
            ).order_by('-created_at')[:5]
            
        except Exception as e:
            logger.error(f"Error loading assignments: {e}")
            context["assignment_progress"] = 0
            context["completed_assignments_count"] = 0
            context["total_assignments_count"] = 0

        try:
            # Calculate log progress based on virtual logbook activities
            if intern_obj:
                virtual_logbook = VirtualLogbook.objects.filter(intern=intern_obj).first()
                if virtual_logbook:
                    total_activities = virtual_logbook.activities.count()
                    approved_activities = virtual_logbook.activities.filter(is_approved=True).count()
                    
                    if total_activities > 0:
                        context["log_progress"] = int((approved_activities / total_activities) * 100)
                    else:
                        context["log_progress"] = 0
                else:
                    context["log_progress"] = 0
            else:
                context["log_progress"] = 0
                
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
            context["log_progress"] = 0

        context["pending_approval"] = max(0, 100 - context["assignment_progress"])

        try:
            seven_days_ago = today - timedelta(days=7)
            
            # Virtual logbook activities
            if intern_obj:
                virtual_logbook = VirtualLogbook.objects.filter(intern=intern_obj).first()
                if virtual_logbook:
                    recent_activities = virtual_logbook.activities.filter(
                        created_at__gte=seven_days_ago
                    ).order_by('-created_at')[:5]
                    
                    for activity in recent_activities:
                        status = "approved" if activity.is_approved else "submitted"
                        context["recent_activities"].append({
                            'description': f"Logbook activity {status}: {activity.description[:50]}...",
                            'timestamp': activity.created_at,
                            'icon': 'bi-journal-text'
                        })
            
            # Assignment activities
            from elogbook.apps.assignments.models import Assignment
            recent_assign_activities = Assignment.objects.filter(
                intern=intern_obj,
                created_at__gte=seven_days_ago
            ).order_by('-created_at')[:5]
            
            for assignment in recent_assign_activities:
                action = "submitted" if assignment.status == 'submitted' else "completed"
                context["recent_activities"].append({
                    'description': f"{action} assignment: {assignment.title}",
                    'timestamp': assignment.created_at,
                    'icon': 'bi-list-task'
                })
            
            context["recent_activities"].sort(key=lambda x: x['timestamp'], reverse=True)
            context["recent_activities"] = context["recent_activities"][:5]  
            
        except Exception as e:
            logger.error(f"Error loading recent activities: {e}")

        try:
            from elogbook.apps.assignments.models import Assignment
            pending_assignments = Assignment.objects.filter(
                intern=intern_obj,
                status='submitted'
            ).count()
            
            # Count pending virtual logbook activities
            pending_logs = 0
            if intern_obj:
                virtual_logbook = VirtualLogbook.objects.filter(intern=intern_obj).first()
                if virtual_logbook:
                    pending_logs = virtual_logbook.activities.filter(is_approved=False).count()
            
            context["pending_reviews_count"] = pending_assignments + pending_logs
            
        except Exception as e:
            logger.error(f"Error counting pending reviews: {e}")

    return render(request, "accounts/dashboard.html", context)


@login_required
def dashboard_data(request):
    """API endpoint for real-time dashboard data updates"""
    from django.http import JsonResponse
    
    user = request.user
    intern_obj = getattr(user, "intern_profile", None)
    
    # Calculate logbook statistics using virtual logbook
    total_weeks = 8
    completed_logbooks = 0
    weeks_remaining = 0
    
    if intern_obj:
        try:
            virtual_logbook = VirtualLogbook.objects.get(intern=intern_obj)
            completed_logbooks = virtual_logbook.get_approved_weeks().count()
        except VirtualLogbook.DoesNotExist:
            completed_logbooks = 0
            
        # Calculate weeks remaining based on virtual logbook uploads
        if intern_obj.end_date:
            today = timezone.now().date()
            days_remaining = (intern_obj.end_date - today).days
            
            # Calculate weeks remaining based on virtual logbook uploads
            total_weeks = 8
            try:
                virtual_logbook = VirtualLogbook.objects.get(intern=intern_obj)
                uploaded_weeks = virtual_logbook.get_approved_weeks().count()
                weeks_remaining = max(0, total_weeks - uploaded_weeks)
            except VirtualLogbook.DoesNotExist:
                weeks_remaining = total_weeks
    
    # Calculate logbook progress percentage
    logbook_progress = min(100, int((completed_logbooks / total_weeks) * 100)) if total_weeks > 0 else 0
    
    # Assignment progress
    assignment_progress = 0
    log_progress = 0
    
    if intern_obj:
        try:
            from elogbook.apps.assignments.models import Assignment
            total_assignments = Assignment.objects.filter(intern=intern_obj).count()
            completed_assignments = Assignment.objects.filter(
                intern=intern_obj, 
                status='approved'
            ).count()
            
            if total_assignments > 0:
                assignment_progress = int((completed_assignments / total_assignments) * 100)
            
            submitted_assignments = Assignment.objects.filter(
                intern=intern_obj, 
                status__in=['submitted', 'approved']
            ).count()
        except Exception:
            assignment_progress = 0
            total_assignments = 0
            submitted_assignments = 0
        
        try:
            # Calculate log progress based on virtual logbook activities
            virtual_logbook = VirtualLogbook.objects.filter(intern=intern_obj).first()
            if virtual_logbook:
                total_activities = virtual_logbook.activities.count()
                approved_activities = virtual_logbook.activities.filter(is_approved=True).count()
                
                if total_activities > 0:
                    log_progress = int((approved_activities / total_activities) * 100)
        except Exception:
            log_progress = 0
    
    pending_approval = max(0, 100 - assignment_progress)
    
    return JsonResponse({
        'logbook_progress': logbook_progress,
        'completed_logbooks': completed_logbooks,
        'total_weeks': total_weeks,
        'assignment_progress': assignment_progress,
        'log_progress': log_progress,
        'pending_approval': pending_approval,
        'completed_assignments_count': submitted_assignments,
        'total_assignments_count': total_assignments,
        'weeks_remaining': weeks_remaining,
        'days_remaining': days_remaining if intern_obj and intern_obj.end_date else 0,
    })


def profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {"user": request.user})


@login_required
def settings(request):
    user = request.user

    if request.method == 'POST':
        form = UserSettingsForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Settings saved successfully.')
            response = redirect('accounts:settings')
            # Persist theme choice to a cookie so non-auth pages (login) can also pick it up.
            try:
                response.set_cookie('site_theme', user.theme or 'light', max_age=30*24*3600)
            except Exception:
                pass
            return response
    else:
        form = UserSettingsForm(instance=user)

    return render(request, 'accounts/settings.html', {"user": user, 'form': form})


@login_required
def delete_account(request):
    user = request.user
    if request.method == 'POST':
        # Soft-delete: mark inactive and logout
        user.is_active = False
        user.save()
        logout(request)
        messages.success(request, 'Your account has been deactivated.')
        return redirect('accounts:home')

    return render(request, 'accounts/confirm_delete.html', {"user": user})


@login_required
def remove_profile_picture(request):
    user = request.user
    if request.method != 'POST':
        return HttpResponseForbidden()

    if user.profile_picture:
        user.profile_picture.delete(save=False)
        user.profile_picture = None
        user.save()
        messages.success(request, 'Profile picture removed.')

    return redirect('accounts:settings')


@login_required
def help_center(request):
    """Help & Support Center for interns."""
    user = request.user
    intern_obj = getattr(user, "intern_profile", None)
    supervisor = getattr(intern_obj, "supervisor", None) if intern_obj else None

    context = {
        "user": user,
        "supervisor": supervisor,
        "current_date": timezone.now().strftime("%B %d, %Y"),
    }

    return render(request, 'accounts/help.html', context)

def submitassignment(request, pk):
    # Get the assignment instance
    assignment = AssignmentModal.objects.get(id=pk)
    form = AssignmentSubmissionForm()

    if request.method == "POST":
        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.intern = request.user           # save logged-in user
            submission.assignment = assignment   
            assignment.is_submitted = True      # save the assignment
            submission.save()

            messages.success(request, "Assignment submitted successfully.")
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Error submitting your assignment.")
    else:
        form = AssignmentSubmissionForm()

    context = {
        "form": form,
    }
    return render(request, "accounts/submit_assignment.html", context)