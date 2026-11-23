from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os

def logbook_template_path(instance, filename):
    return f'logbooks/templates/{filename}'

def student_logbook_path(instance, filename):
    return f'logbooks/students/{instance.student.id}/{filename}'

class LogbookTemplate(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    word_file = models.FileField(
        upload_to=logbook_template_path,
        storage=FileSystemStorage(),
        help_text="Upload a Word document (.docx) template for the logbook"
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class StudentLogbook(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('changes_requested', 'Changes Requested'),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_logbooks'
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supervisor_logbooks',
        null=True,
        blank=True
    )
    template = models.ForeignKey(LogbookTemplate, on_delete=models.CASCADE)
    word_file = models.FileField(
        upload_to=student_logbook_path,
        storage=FileSystemStorage(),
        null=True,
        blank=True
    )
    pdf_file = models.FileField(
        upload_to=student_logbook_path,
        storage=FileSystemStorage(),
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    supervisor_feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.template.name}"

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['student', 'template']

class VirtualLogbook(models.Model):
    """Virtual logbook that tracks approved weekly entries for each intern"""
    intern = models.OneToOneField(
        'accounts.Intern',
        on_delete=models.CASCADE,
        related_name='virtual_logbook'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Virtual Logbook - {self.intern.user.get_full_name()}"

    def get_approved_weeks(self):
        """Get all approved weekly entries ordered by week number"""
        return self.weekly_entries.filter(is_approved=True).order_by('week_number')
    
    def get_all_weeks(self):
        """Get all weekly entries (approved and rejected) ordered by week number"""
        return self.weekly_entries.all().order_by('week_number')

    def get_next_week_number(self):
        """Get the next week number for a new entry"""
        last_week = self.weekly_entries.aggregate(
            max_week=models.Max('week_number')
        )['max_week']
        return (last_week or 0) + 1

    class Meta:
        verbose_name = "Virtual Logbook"
        verbose_name_plural = "Virtual Logbooks"

class WeeklyLogbookEntry(models.Model):
    """Individual weekly entries in the virtual logbook"""
    virtual_logbook = models.ForeignKey(
        VirtualLogbook,
        on_delete=models.CASCADE,
        related_name='weekly_entries'
    )
    week_number = models.PositiveIntegerField()
    student_logbook = models.ForeignKey(
        StudentLogbook,
        on_delete=models.CASCADE,
        related_name='weekly_entries',
        help_text="The StudentLogbook that created this weekly entry"
    )
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    supervisor_feedback = models.TextField(blank=True, help_text="Supervisor feedback specific to this weekly entry")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_weekly_entries'
    )
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_weekly_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # New rich fields for PT report
    # Main job of the week (one-to-one; optional until intern fills)
    # Will be defined below and linked via OneToOne relationships

    def __str__(self):
        return f"Week {self.week_number} - {self.virtual_logbook.intern.user.get_full_name()}"

    class Meta:
        ordering = ['week_number']
        unique_together = ['virtual_logbook', 'week_number']
        verbose_name = "Weekly Logbook Entry"
        verbose_name_plural = "Weekly Logbook Entries"


class DailyActivity(models.Model):
    """Daily activities (Mon-Fri) for a weekly entry"""
    weekly_entry = models.ForeignKey(
        WeeklyLogbookEntry,
        on_delete=models.CASCADE,
        related_name='daily_activities'
    )
    date = models.DateField()
    summary = models.TextField()

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.date} - {self.weekly_entry}"


class MainJobOfWeek(models.Model):
    weekly_entry = models.OneToOneField(
        WeeklyLogbookEntry,
        on_delete=models.CASCADE,
        related_name='main_job'
    )
    task_title = models.CharField(max_length=255)
    step_by_step = models.JSONField(default=list, blank=True)
    tools_used = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Main Job - {self.weekly_entry}"


def diagram_upload_path(instance, filename):
    """Upload path for diagram images/signatures/stamps per intern/week."""
    intern_id = instance.weekly_entry.virtual_logbook.intern.id
    return f'logbooks/diagrams/{intern_id}/{filename}'


class DiagrammaticPresentation(models.Model):
    weekly_entry = models.OneToOneField(
        WeeklyLogbookEntry,
        on_delete=models.CASCADE,
        related_name='diagram'
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=diagram_upload_path, null=True, blank=True)
    supervisor_checked = models.BooleanField(default=False)
    supervisor_signature = models.ImageField(upload_to=diagram_upload_path, null=True, blank=True)
    official_stamp = models.ImageField(upload_to=diagram_upload_path, null=True, blank=True)

    def __str__(self):
        return f"Diagram - {self.weekly_entry}"