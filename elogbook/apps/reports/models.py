from django.db import models
from django.conf import settings
from elogbook.apps.logbook.models import StudentLogbook
# SupervisorProfile model doesn't exist yet
# from elogbook.apps.supervision.models import SupervisorProfile

def report_file_path(instance, filename):
    # Generate a file path for report PDF files
    return f'reports/{instance.intern.username}/{filename}'

def signature_file_path(instance, filename):
    # Generate a file path for signature files
    return f'signatures/{instance.intern.username}/{filename}'

class Report(models.Model):
    REPORT_STATUS = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('signed', 'Signed'),
        ('exported', 'Exported')
    ]

    intern = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='draft')
    introduction = models.TextField(blank=True, null=True)
    conclusion = models.TextField(blank=True, null=True)
    table_of_contents = models.JSONField(default=dict, blank=True)
    supervisor_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    generated_pdf = models.FileField(upload_to='reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'

    def __str__(self):
        return f"{self.intern.username}'s Report - {self.created_at.strftime('%Y-%m-%d')}"


class MainReport(models.Model):
    """Main PT Report master data linked to an intern."""
    intern = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='main_reports')
    # Company profile
    company_intro = models.TextField(blank=True, default='')
    organizational_chart = models.ImageField(upload_to='report-assets/', null=True, blank=True)
    safety_regulations = models.TextField(blank=True, default='')
    recruitment_policies = models.TextField(blank=True, default='')

    # Main task section
    main_title = models.CharField(max_length=255, blank=True, default='')
    problem_definition = models.TextField(blank=True, default='')
    proposed_solution = models.TextField(blank=True, default='')
    solution_justification = models.TextField(blank=True, default='')
    alternative_solutions = models.TextField(blank=True, default='')
    challenges_encountered = models.TextField(blank=True, default='')
    conclusion = models.TextField(blank=True, default='')
    recommendations = models.TextField(blank=True, default='')
    references = models.JSONField(default=list, blank=True)

    is_final_pt = models.BooleanField(default=False)

    # Generated artifacts (optional)
    generated_docx = models.FileField(upload_to='reports/', null=True, blank=True)
    generated_pdf = models.FileField(upload_to='reports/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Main Report'
        verbose_name_plural = 'Main Reports'

    def __str__(self):
        return f"MainReport for {self.intern.username} ({'Final' if self.is_final_pt else 'Interim'})"

class ReportSection(models.Model):
    SECTION_TYPES = [
        ('cover', 'Cover Page'),
        ('introduction', 'Introduction'),
        ('logbook', 'Logbook Entry'),
        ('supervisor_comment', 'Supervisor Comment'),
        ('conclusion', 'Conclusion'),
        ('signature', 'Signature')
    ]

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES)
    order = models.PositiveIntegerField(default=0)
    logbook_entry = models.ForeignKey(StudentLogbook, null=True, blank=True, on_delete=models.SET_NULL, related_name='report_sections')
    supervisor_comment = models.TextField(blank=True, null=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Report Section'
        verbose_name_plural = 'Report Sections'

    def __str__(self):
        return f"{self.report.title} - {self.title}"
