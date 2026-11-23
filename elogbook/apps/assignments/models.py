from django.db import models
from django.conf import settings
from django.utils import timezone


def assignment_upload_path(instance, filename):
    return f'assignments/{instance.intern.id}/{filename}'


def submission_upload_path(instance, filename):
    return f'assignment_submissions/{instance.assignment.intern.id}/{filename}'


class Assignment(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Needs Revision'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    intern = models.ForeignKey(
        'accounts.Intern',
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    supervisor = models.ForeignKey(
        'accounts.Supervisor',
        on_delete=models.CASCADE,
        related_name="created_assignments"
    )
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    assignment_file = models.FileField(upload_to=assignment_upload_path, blank=True, null=True, help_text="Optional file attachment from supervisor")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.intern.user.get_full_name()}"
    
    @property
    def is_overdue(self):
        return timezone.now() > self.deadline and self.status == 'assigned'


class AssignmentSubmission(models.Model):
    assignment = models.OneToOneField(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submission'
    )
    submission_file = models.FileField(upload_to=submission_upload_path)
    notes = models.TextField(blank=True, help_text="Optional notes from intern")
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Review fields
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_submissions'
    )
    supervisor_feedback = models.TextField(blank=True)
    grade = models.CharField(max_length=10, blank=True, help_text="Grade assigned by supervisor")
    
    def __str__(self):
        return f"Submission for {self.assignment.title}"


# Keep old model name for backward compatibility
AssignmentModal = Assignment

