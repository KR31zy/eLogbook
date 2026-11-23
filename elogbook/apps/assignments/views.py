from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, Http404
from .models import Assignment, AssignmentSubmission
from .forms import AssignmentSubmissionForm, AssignmentCreateForm, AssignmentReviewForm
from elogbook.apps.accounts.models import Intern, Supervisor, User

# Helper function to check if user is a supervisor
def is_supervisor(user):
    return user.is_authenticated and user.role == User.Role.SUPERVISOR

# Helper function to check if user is an intern
def is_intern(user):
    return user.is_authenticated and user.role == User.Role.INTERN

@login_required
@user_passes_test(is_intern)
def intern_assignments(request):
    try:
        intern = Intern.objects.get(user=request.user)
        assignments = Assignment.objects.filter(intern=intern).prefetch_related('submission')
    except Intern.DoesNotExist:
        messages.error(request, 'You do not have an intern profile. Please contact an administrator.')
        assignments = []
    
    return render(request, 'assignments/intern_assignments.html', {
        'assignments': assignments
    })

@login_required
@user_passes_test(is_supervisor)
def supervisor_dashboard(request):
    try:
        supervisor = Supervisor.objects.get(user=request.user)
        assignments = Assignment.objects.all()
    except Supervisor.DoesNotExist:
        messages.error(request, 'You do not have a supervisor profile. Please contact an administrator.')
        assignments = []
    
    return render(request, 'assignments/supervisor_dashboard.html', {
        'assignments': assignments
    })

@login_required
@user_passes_test(is_supervisor)
def create_assignment(request):
    try:
        supervisor = Supervisor.objects.get(user=request.user)
    except Supervisor.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('accounts:dashboard')
        
    if request.method == 'POST':
        form = AssignmentCreateForm(request.POST, request.FILES, supervisor=supervisor)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.supervisor = supervisor
            assignment.save()
            messages.success(request, f'Assignment "{assignment.title}" created and assigned to {assignment.intern.user.get_full_name()}.')
            return redirect('assignments:supervisor_dashboard')
    else:
        form = AssignmentCreateForm(supervisor=supervisor)
    
    return render(request, 'assignments/create_assignment.html', {
        'form': form
    })

@login_required
@user_passes_test(is_supervisor)
def update_assignment(request, assignment_id):
    try:
        supervisor = Supervisor.objects.get(user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id, supervisor=supervisor)
    except Supervisor.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = AssignmentCreateForm(request.POST, request.FILES, instance=assignment, supervisor=supervisor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated successfully.')
            return redirect('assignments:supervisor_dashboard')
    else:
        form = AssignmentCreateForm(instance=assignment, supervisor=supervisor)
    
    return render(request, 'assignments/update_assignment.html', {
        'form': form,
        'assignment': assignment
    })

@login_required
@user_passes_test(is_supervisor)
def delete_assignment(request, assignment_id):
    try:
        supervisor = Supervisor.objects.get(user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id, supervisor=supervisor)
    except Supervisor.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully.')
        return redirect('assignments:supervisor_dashboard')
    
    return render(request, 'assignments/delete_assignment.html', {
        'assignment': assignment
    })


@login_required
@user_passes_test(is_intern)
def submit_assignment(request, assignment_id):
    try:
        intern = Intern.objects.get(user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id, intern=intern)
    except Intern.DoesNotExist:
        messages.error(request, 'Intern profile not found.')
        return redirect('accounts:dashboard')
    
    # Check if already submitted
    if hasattr(assignment, 'submission'):
        messages.info(request, 'You have already submitted this assignment.')
        return redirect('assignments:intern_assignments')
    
    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.save()
            
            # Update assignment status
            assignment.status = 'submitted'
            assignment.save()
            
            messages.success(request, f'Assignment "{assignment.title}" submitted successfully!')
            return redirect('assignments:intern_assignments')
    else:
        form = AssignmentSubmissionForm()
    
    return render(request, 'assignments/submit_assignment.html', {
        'form': form,
        'assignment': assignment
    })


@login_required
@user_passes_test(is_supervisor)
def review_submission(request, assignment_id):
    try:
        supervisor = Supervisor.objects.get(user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id, supervisor=supervisor)
        submission = get_object_or_404(AssignmentSubmission, assignment=assignment)
    except Supervisor.DoesNotExist:
        messages.error(request, 'Supervisor profile not found.')
        return redirect('accounts:dashboard')
    except AssignmentSubmission.DoesNotExist:
        messages.error(request, 'No submission found for this assignment.')
        return redirect('assignments:supervisor_dashboard')
    
    if request.method == 'POST':
        form = AssignmentReviewForm(request.POST, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.reviewed_at = timezone.now()
            submission.reviewed_by = request.user
            
            # Update assignment status based on review decision
            review_decision = form.cleaned_data['review_decision']
            assignment.status = review_decision
            assignment.save()
            
            submission.save()
            
            action = 'approved' if review_decision == 'approved' else 'returned for revision'
            messages.success(request, f'Assignment "{assignment.title}" has been {action}.')
            return redirect('assignments:supervisor_dashboard')
    else:
        form = AssignmentReviewForm(instance=submission)
    
    return render(request, 'assignments/review_submission.html', {
        'form': form,
        'assignment': assignment,
        'submission': submission
    })


@login_required
def download_assignment_file(request, assignment_id):
    try:
        if request.user.role == User.Role.INTERN:
            intern = Intern.objects.get(user=request.user)
            assignment = get_object_or_404(Assignment, id=assignment_id, intern=intern)
        elif request.user.role == User.Role.SUPERVISOR:
            supervisor = Supervisor.objects.get(user=request.user)
            assignment = get_object_or_404(Assignment, id=assignment_id, supervisor=supervisor)
        else:
            raise Http404()
    except (Intern.DoesNotExist, Supervisor.DoesNotExist):
        raise Http404()
    
    if not assignment.assignment_file:
        raise Http404()
    
    response = HttpResponse(assignment.assignment_file.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{assignment.assignment_file.name.split("/")[-1]}"'
    return response


@login_required
def download_submission_file(request, assignment_id):
    try:
        if request.user.role == User.Role.INTERN:
            intern = Intern.objects.get(user=request.user)
            assignment = get_object_or_404(Assignment, id=assignment_id, intern=intern)
        elif request.user.role == User.Role.SUPERVISOR:
            supervisor = Supervisor.objects.get(user=request.user)
            assignment = get_object_or_404(Assignment, id=assignment_id, supervisor=supervisor)
        else:
            raise Http404()
            
        submission = get_object_or_404(AssignmentSubmission, assignment=assignment)
    except (Intern.DoesNotExist, Supervisor.DoesNotExist, AssignmentSubmission.DoesNotExist):
        raise Http404()
    
    response = HttpResponse(submission.submission_file.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{submission.submission_file.name.split("/")[-1]}"'
    return response

