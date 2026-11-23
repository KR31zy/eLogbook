import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.db import transaction
import json

from elogbook.apps.accounts.models import User, Intern, Supervisor, SubmittedAssignment
from elogbook.apps.logbook.models import StudentLogbook, LogbookTemplate
from elogbook.apps.assignments.models import AssignmentModal

logger = logging.getLogger(__name__)


# Authentication Decorators
def is_intern(view_func):
    """Decorator to ensure user is an intern"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not hasattr(request.user, 'intern_profile'):
            return JsonResponse({'error': 'Intern access required'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def is_supervisor(view_func):
    """Decorator to ensure user is a supervisor"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not hasattr(request.user, 'supervisor_profile'):
            return JsonResponse({'error': 'Supervisor access required'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


# Intern Logbook Functions
@csrf_exempt
@require_http_methods(["POST"])
@login_required
@is_intern
def submit_logbook(request):
    """An intern can submit a new logbook entry"""
    try:
        data = json.loads(request.body)
        intern = request.user.intern_profile
        
        # Get template
        template_id = data.get('template_id')
        if not template_id:
            return JsonResponse({'error': 'Template ID is required'}, status=400)
        
        try:
            template = LogbookTemplate.objects.get(id=template_id)
        except LogbookTemplate.DoesNotExist:
            return JsonResponse({'error': 'Template not found'}, status=404)
        
        # Create or update logbook entry
        with transaction.atomic():
            logbook, created = StudentLogbook.objects.get_or_create(
                student=request.user,
                template=template,
                defaults={
                    'content': data.get('content', ''),
                    'status': 'submitted',
                    'submitted_at': timezone.now(),
                    'supervisor_id': intern.supervisor_id if intern.supervisor else None
                }
            )
            
            if not created:
                # Update existing logbook
                logbook.content = data.get('content', logbook.content)
                logbook.status = 'submitted'
                logbook.submitted_at = timezone.now()
                logbook.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Logbook submitted successfully',
            'logbook_id': logbook.id
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error submitting logbook: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
@login_required
@is_intern
def get_intern_logbooks(request):
    """Fetch all logbooks submitted by the currently authenticated intern"""
    try:
        logbooks = StudentLogbook.objects.filter(
            student=request.user
        ).select_related('template', 'supervisor').order_by('-submitted_at')
        
        logbooks_data = []
        for logbook in logbooks:
            logbooks_data.append({
                'id': logbook.id,
                'template_name': logbook.template.name if logbook.template else 'Unknown',
                'content': logbook.content,
                'status': logbook.status,
                'submitted_at': logbook.submitted_at.isoformat() if logbook.submitted_at else None,
                'supervisor_feedback': logbook.supervisor_feedback,
                'reviewed_at': logbook.reviewed_at.isoformat() if logbook.reviewed_at else None
            })
        
        return JsonResponse({
            'success': True,
            'logbooks': logbooks_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching intern logbooks: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# Assignment Submission Functions
@csrf_exempt
@require_http_methods(["POST"])
@login_required
@is_intern
def submit_assignment(request):
    """An intern submits an assignment solution"""
    try:
        data = json.loads(request.body)
        intern = request.user.intern_profile
        
        assignment_id = data.get('assignment_id')
        solution_content = data.get('solution_content', '')
        
        if not assignment_id:
            return JsonResponse({'error': 'Assignment ID is required'}, status=400)
        
        try:
            assignment = AssignmentModal.objects.get(
                id=assignment_id,
                intern=intern
            )
        except AssignmentModal.DoesNotExist:
            return JsonResponse({'error': 'Assignment not found or not assigned to you'}, status=404)
        
        # Create or update submission
        with transaction.atomic():
            submission, created = SubmittedAssignment.objects.get_or_create(
                assignment=assignment,
                intern=request.user,
                defaults={
                    'comments': solution_content,
                    'submitted_at': timezone.now()
                }
            )
            
            if not created:
                submission.comments = solution_content
                submission.submitted_at = timezone.now()
                submission.save()
            
            # Update assignment status
            assignment.status = 'submitted'
            assignment.is_submitted = True
            assignment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Assignment submitted successfully',
            'submission_id': submission.id
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error submitting assignment: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
@login_required
@is_intern
def get_intern_assignments(request):
    """Fetch all assignments where the internId matches the currently authenticated intern"""
    try:
        intern = request.user.intern_profile
        assignments = AssignmentModal.objects.filter(
            intern=intern
        ).select_related('intern__user').order_by('-deadline')
        
        assignments_data = []
        for assignment in assignments:
            # Get latest submission if exists
            latest_submission = assignment.submissions.order_by('-submitted_at').first()
            
            assignments_data.append({
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'deadline': assignment.deadline.isoformat() if assignment.deadline else None,
                'status': assignment.status,
                'is_submitted': assignment.is_submitted,
                'created_at': assignment.created_at.isoformat() if hasattr(assignment, 'created_at') else None,
                'latest_submission': {
                    'id': latest_submission.id,
                    'solution_content': latest_submission.comments,
                    'submitted_at': latest_submission.submitted_at.isoformat(),
                    'comments': latest_submission.comments
                } if latest_submission else None
            })
        
        return JsonResponse({
            'success': True,
            'assignments': assignments_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching intern assignments: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
