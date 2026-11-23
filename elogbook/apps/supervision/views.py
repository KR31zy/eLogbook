import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.db.models import Q
from elogbook.apps.logbook.models import StudentLogbook
from elogbook.apps.assignments.models import Assignment
from elogbook.apps.accounts.models import Supervisor, Intern, User
from .forms import AssignmentCreateForm

logger = logging.getLogger(__name__)


class SupervisorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Ensure the user is an authenticated supervisor and provide helpers."""

    def test_func(self):
        user = self.request.user
        role = str(getattr(user, "role", "")).upper()
        return (
            user.is_authenticated
            and role == getattr(User.Role, 'SUPERVISOR', 'SUPERVISOR')
            and hasattr(user, "supervisor_profile")
        )

    def handle_no_permission(self):
        messages.error(self.request, "Supervisor access required.")
        return redirect("accounts:dashboard")

    def get_supervisor(self):
        try:
            return self.request.user.supervisor_profile
        except AttributeError:
            return None

    def get_interns_qs(self):
        supervisor = self.get_supervisor()
        if supervisor:
            return (
                Intern.objects.filter(supervisor=supervisor)
                .select_related("user")
                .order_by("user__first_name", "user__last_name")
            )
        return Intern.objects.none()


class SupervisorDashboardView(SupervisorRequiredMixin, TemplateView):
    template_name = "supervision/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        supervisor = self.get_supervisor()
        interns = self.get_interns_qs()
        intern_user_ids = interns.values_list("user_id", flat=True)
        
        # Debug logging
        print(f"DEBUG: Supervisor: {supervisor}")
        print(f"DEBUG: Interns count: {interns.count()}")
        for intern in interns:
            print(f"DEBUG: Intern: {intern.user.username} - {intern.user.get_full_name()}")

        pending_logbooks = (
            StudentLogbook.objects.filter(
                student_id__in=intern_user_ids, status__iexact="submitted"
            )
            .select_related("student")
            .order_by("-submitted_at")[:10]
        )

        pending_assignments = (
            Assignment.objects.filter(intern__in=interns)
            .filter(status__iexact="submitted")
            .select_related("intern", "intern__user")
            .order_by("-deadline")[:10]
        )

        ctx.update(
            {
                "supervisor": supervisor,
                "interns": interns,
                "stats": {
                    "intern_count": interns.count(),
                    "pending_logbooks_count": pending_logbooks.count(),
                    "pending_assignments_count": pending_assignments.count(),
                },
                "pending_logbooks": pending_logbooks,
                "pending_assignments": pending_assignments,
                "now": timezone.now(),
            }
        )
        return ctx


class LogbookListView(SupervisorRequiredMixin, ListView):
    model = StudentLogbook
    template_name = "supervision/logbook_list.html"
    context_object_name = "logbooks"
    paginate_by = 20

    def get_queryset(self):
        interns = self.get_interns_qs()
        intern_user_ids = interns.values_list("user_id", flat=True)
        qs = (
            StudentLogbook.objects.filter(student_id__in=intern_user_ids)
            .select_related("student")
            .order_by("-submitted_at", "-updated_at", "-created_at")
        )
        status = self.request.GET.get("status")
        if status and status.lower() != "all":
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_filter"] = self.request.GET.get("status") or "all"
        ctx["status_choices"] = ["all", "draft", "submitted", "under_review", "approved", "changes_requested"]
        return ctx


class LogbookReviewView(SupervisorRequiredMixin, DetailView):
    model = StudentLogbook
    template_name = "supervision/logbook_review.html"
    context_object_name = "logbook"

    def get_queryset(self):
        interns = self.get_interns_qs()
        intern_user_ids = interns.values_list("user_id", flat=True)
        return (
            StudentLogbook.objects.filter(student_id__in=intern_user_ids)
            .select_related("student", "template")
            .order_by("-submitted_at")
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get("action")
        feedback = request.POST.get("feedback", "").strip()

        if feedback:
            self.object.supervisor_feedback = feedback

        if action == "approve":
            self.object.status = "approved"
            messages.success(request, "Logbook approved.")
        elif action == "reject":
            self.object.status = "changes_requested"
            messages.warning(request, "Logbook changes requested.")
        else:
            messages.error(request, "Invalid action.")
            return redirect("supervision:logbooks-review", pk=self.object.pk)

        self.object.reviewed_at = timezone.now()
        if not self.object.supervisor_id:
            self.object.supervisor_id = request.user.id
        self.object.save()
        return redirect("supervision:logbooks")


class AssignmentListView(SupervisorRequiredMixin, ListView):
    model = Assignment
    template_name = "supervision/assignment_list.html"
    context_object_name = "assignments"
    paginate_by = 20

    def get_queryset(self):
        interns = self.get_interns_qs()
        qs = (
            Assignment.objects.filter(intern__in=interns)
            .select_related("intern", "intern__user")
            .order_by("-deadline", "-id")
        )
        status = self.request.GET.get("status")
        if status and status.lower() != "all":
            qs = qs.filter(status=status)
        return qs


class AssignmentCreateView(SupervisorRequiredMixin, CreateView):
    model = Assignment
    form_class = AssignmentCreateForm
    template_name = "supervision/assignment_form.html"
    success_url = reverse_lazy("supervision:assignments")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["supervisor"] = self.get_supervisor()
        return kwargs

    def form_valid(self, form):
        assignment = form.save(commit=False)
        assignment.supervisor = self.get_supervisor()
        assignment.save()
        messages.success(self.request, "Assignment created.")
        return redirect(self.success_url)


class AssignmentReviewView(SupervisorRequiredMixin, DetailView):
    model = Assignment
    template_name = "supervision/assignment_review.html"
    context_object_name = "assignment"

    def get_queryset(self):
        interns = self.get_interns_qs()
        return (
            Assignment.objects.filter(intern__in=interns)
            .select_related("intern", "intern__user")
            .prefetch_related("submission")
            .order_by("-deadline", "-id")
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the submission for this assignment
        try:
            context['submission'] = self.object.submission
        except:
            context['submission'] = None
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        new_status = request.POST.get("status")  # expected statuses from form
        feedback = request.POST.get("feedback", "").strip()
        grade = request.POST.get("grade", "").strip()

        if new_status:
            self.object.status = new_status
            if new_status.lower() in ("reviewed", "completed", "approved"):
                self.object.is_submitted = False
            self.object.save()

        # Attach feedback/grade to the submission if available
        try:
            submission = self.object.submission
            if submission and (feedback or grade):
                if feedback:
                    submission.supervisor_feedback = feedback
                if grade:
                    submission.grade = grade
                submission.reviewed_at = timezone.now()
                submission.reviewed_by = request.user
                submission.save()
                
                # Send notification to intern about the review
                self._send_assignment_notification(submission, new_status, feedback, grade)
        except:
            pass

        messages.success(request, "Assignment review saved.")
        return redirect("supervision:assignments")
    
    def _send_assignment_notification(self, submission, status, feedback, grade):
        """Send notification to intern about assignment review"""
        from elogbook.apps.notifications.models import Message
        
        assignment = submission.assignment
        intern_user = assignment.intern.user
        supervisor_user = self.request.user
        
        # Create notification message
        status_text = {
            'approved': 'approved',
            'rejected': 'needs revision',
            'submitted': 'under review'
        }.get(status, status)
        
        content_parts = [
            f"Your assignment '{assignment.title}' has been reviewed and is now {status_text}."
        ]
        
        if grade:
            content_parts.append(f"Grade: {grade}")
            
        if feedback:
            content_parts.append(f"Supervisor Feedback: {feedback}")
            
        if status == 'rejected':
            content_parts.append("Please review the feedback and resubmit your work.")
        elif status == 'approved':
            content_parts.append("Congratulations on completing this assignment!")
            
        notification_content = "\n\n".join(content_parts)
        
        # Create the notification
        Message.objects.create(
            sender=supervisor_user,
            recipient=intern_user,
            content=notification_content
        )
