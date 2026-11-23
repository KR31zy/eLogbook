import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
import json

from elogbook.apps.accounts.models import User, Intern, Supervisor, SubmittedAssignment
from elogbook.apps.logbook.models import StudentLogbook
from elogbook.apps.assignments.models import AssignmentModal

logger = logging.getLogger(__name__)


def is_supervisor(view_func):
    """Decorator to ensure user is a supervisor"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if not hasattr(request.user, 'supervisor_profile'):
            return JsonResponse({'error': 'Supervisor access required'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper


# Supervisor Assignment Functions
@csrf_exempt
@require_http_methods(["POST"])
@login_required
@is_supervisor
def create_assignment(request):
    """A supervisor can create a new assignment"""
    try:
        data = json.loads(request.body)
        supervisor = request.user.supervisor_profile
        
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        intern_id = data.get('intern_id')
        deadline = data.get('deadline')
        
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)
        
        if not description:
            return JsonResponse({'error': 'Description is required'}, status=400)
        
        if not intern_id:
            return JsonResponse({'error': 'Intern ID is required'}, status=400)
        
        # Verify intern belongs to this supervisor
        try:
            intern = Intern.objects.get(
                id=intern_id,
                supervisor=supervisor
            )
        except Intern.DoesNotExist:
            return JsonResponse({'error': 'Intern not found or not under your supervision'}, status=404)
        
        # Parse deadline if provided
        deadline_obj = None
        if deadline:
            try:
                from datetime import datetime
                deadline_obj = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except ValueError:
                return JsonResponse({'error': 'Invalid deadline format'}, status=400)
        
        # Create assignment
        with transaction.atomic():
            assignment = AssignmentModal.objects.create(
                title=title,
                description=description,
                intern=intern,
                deadline=deadline_obj,
                created_by=request.user,
                status='pending'
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Assignment created successfully',
            'assignment_id': assignment.id,
            'assignment': {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'intern_name': intern.user.get_full_name() or intern.user.username,
                'deadline': assignment.deadline.isoformat() if assignment.deadline else None,
                'status': assignment.status,
                'created_at': assignment.created_at.isoformat()
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error creating assignment: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
@login_required
@is_supervisor
def get_supervisor_assignments(request):
    """Fetch all assignments created by the currently authenticated supervisor"""
    try:
        supervisor = request.user.supervisor_profile
        
        # Get all interns under this supervisor
        intern_ids = supervisor.interns.values_list('id', flat=True)
        
        assignments = AssignmentModal.objects.filter(
            intern_id__in=intern_ids
        ).select_related('intern__user').order_by('-created_at')
        
        assignments_data = []
        for assignment in assignments:
            # Get latest submission if exists
            latest_submission = assignment.submissions.order_by('-submitted_at').first()
            
            assignments_data.append({
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'intern_name': assignment.intern.user.get_full_name() or assignment.intern.user.username,
                'intern_id': assignment.intern.id,
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
        logger.error(f"Error fetching supervisor assignments: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# Review Functions
@csrf_exempt
@require_http_methods(["POST"])
@login_required
@is_supervisor
def review_submission(request):
    """A supervisor can review (approve/reject) either a Logbook or an Assignment submission"""
    try:
        data = json.loads(request.body)
        supervisor = request.user.supervisor_profile
        
        submission_id = data.get('id')
        submission_type = data.get('type')  # 'logbook' or 'assignment'
        new_status = data.get('status')  # 'approved' or 'rejected'
        feedback = data.get('feedback', '').strip()
        
        if not submission_id:
            return JsonResponse({'error': 'Submission ID is required'}, status=400)
        
        if submission_type not in ['logbook', 'assignment']:
            return JsonResponse({'error': 'Type must be "logbook" or "assignment"'}, status=400)
        
        if new_status not in ['approved', 'rejected', 'changes_requested']:
            return JsonResponse({'error': 'Status must be "approved", "rejected", or "changes_requested"'}, status=400)
        
        with transaction.atomic():
            if submission_type == 'logbook':
                try:
                    # Get logbook and verify it belongs to supervisor's intern
                    logbook = StudentLogbook.objects.select_related('student__intern_profile').get(
                        id=submission_id,
                        student__intern_profile__supervisor=supervisor
                    )
                    
                    logbook.status = new_status
                    logbook.supervisor_feedback = feedback
                    logbook.reviewed_at = timezone.now()
                    logbook.supervisor = request.user
                    logbook.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Logbook {new_status} successfully',
                        'submission': {
                            'id': logbook.id,
                            'type': 'logbook',
                            'status': logbook.status,
                            'feedback': logbook.supervisor_feedback,
                            'reviewed_at': logbook.reviewed_at.isoformat()
                        }
                    })
                    
                except StudentLogbook.DoesNotExist:
                    return JsonResponse({'error': 'Logbook not found or not under your supervision'}, status=404)
            
            elif submission_type == 'assignment':
                try:
                    # Get assignment submission and verify it belongs to supervisor's intern
                    submission = SubmittedAssignment.objects.select_related(
                        'assignment__intern',
                        'intern'
                    ).get(
                        id=submission_id,
                        intern__intern_profile__supervisor=supervisor
                    )
                    
                    submission.comments = feedback if feedback else submission.comments
                    submission.submitted_at = timezone.now()  # Update timestamp for review
                    submission.save()
                    
                    # Update assignment status as well
                    assignment = submission.assignment
                    if new_status == 'approved':
                        assignment.status = 'completed'
                    elif new_status == 'rejected':
                        assignment.status = 'rejected'
                    else:  # changes_requested
                        assignment.status = 'changes_requested'
                        assignment.is_submitted = False
                    assignment.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Assignment {new_status} successfully',
                        'submission': {
                            'id': submission.id,
                            'type': 'assignment',
                            'status': new_status,
                            'feedback': submission.comments,
                            'reviewed_at': submission.submitted_at.isoformat()
                        }
                    })
                    
                except SubmittedAssignment.DoesNotExist:
                    return JsonResponse({'error': 'Assignment submission not found or not under your supervision'}, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error reviewing submission: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# Pending Submissions Query
@require_http_methods(["GET"])
@login_required
@is_supervisor
def get_pending_submissions(request):
    """Get all logbooks and assignments from supervisor's interns that have status 'submitted'"""
    try:
        supervisor = request.user.supervisor_profile
        
        # Get all interns under this supervisor
        intern_user_ids = supervisor.interns.values_list('user_id', flat=True)
        intern_ids = supervisor.interns.values_list('id', flat=True)
        
        # Get pending logbooks
        pending_logbooks = StudentLogbook.objects.filter(
            student_id__in=intern_user_ids,
            status='submitted'
        ).select_related('student', 'template').order_by('-submitted_at')
        
        # Get pending assignment submissions
        pending_assignments = SubmittedAssignment.objects.filter(
            intern__intern_profile__supervisor=supervisor
        ).select_related('intern', 'assignment').order_by('-submitted_at')
        
        # Format logbooks data
        logbooks_data = []
        for logbook in pending_logbooks:
            logbooks_data.append({
                'id': logbook.id,
                'type': 'logbook',
                'intern_name': logbook.student.get_full_name() or logbook.student.username,
                'intern_id': logbook.student.intern_profile.id if hasattr(logbook.student, 'intern_profile') else None,
                'title': logbook.template.name if logbook.template else 'Logbook Entry',
                'content_preview': logbook.content[:100] + '...' if len(logbook.content) > 100 else logbook.content,
                'submitted_at': logbook.submitted_at.isoformat() if logbook.submitted_at else None,
                'status': logbook.status
            })
        
        # Format assignments data
        assignments_data = []
        for submission in pending_assignments:
            assignments_data.append({
                'id': submission.id,
                'type': 'assignment',
                'intern_name': submission.intern.get_full_name() or submission.intern.username,
                'intern_id': submission.intern.intern_profile.id if hasattr(submission.intern, 'intern_profile') else None,
                'title': submission.assignment.title,
                'assignment_id': submission.assignment.id,
                'solution_preview': submission.comments[:100] + '...' if submission.comments and len(submission.comments) > 100 else submission.comments or '',
                'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                'status': 'submitted',
                'deadline': submission.assignment.deadline.isoformat() if submission.assignment.deadline else None
            })
        
        return JsonResponse({
            'success': True,
            'pending_submissions': {
                'logbooks': logbooks_data,
                'assignments': assignments_data,
                'total_count': len(logbooks_data) + len(assignments_data)
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching pending submissions: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
