from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

from elogbook.apps.assignments.models import AssignmentModal

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        SUPERVISOR = 'SUPERVISOR', 'Supervisor'
        INTERN = 'INTERN', 'Intern'

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.INTERN
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        blank=True, 
        null=True
    )
    # Theme preference (kept)
    theme = models.CharField(choices=[('light', 'Light'), ('dark', 'Dark')], default='light', max_length=10)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_joined']
        verbose_name = "User"
        verbose_name_plural = "Users"

    def save(self, *args, **kwargs):
        if self.role == self.Role.INTERN and not self.username:
            if hasattr(self, 'intern_profile'):
                self.username = self.intern_profile.registration_number
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"


class Supervisor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='supervisor_profile'
    )
    department = models.ForeignKey(
        'institutions.Department',
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='supervisors'
    )
    staff_id = models.CharField(max_length=50, unique=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Supervisor"
        verbose_name_plural = "Supervisors"

    def __str__(self):
        department_name = self.department.name if self.department else 'No Department'
        return f"{self.user.get_full_name()} - {department_name}"


class Intern(models.Model):
    # user = models.ForeignKey(User,
    # on_delete=models.SET_NULL, 
    # )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='intern_profile'
    )
    university = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='interns'
    )
    supervisor = models.ForeignKey(
        'accounts.Supervisor',
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='interns'
    )
    registration_number = models.CharField(max_length=50, unique=True)
    course_name = models.CharField(max_length=200)
    year_of_study = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    expected_outcomes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Intern"
        verbose_name_plural = "Interns"

    def __str__(self):
        return self.user.username if self.user else "No User"



class SubmittedAssignment(models.Model):
    intern = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_assignments')
    assignment = models.ForeignKey(AssignmentModal, on_delete=models.CASCADE, related_name='submissions')
    comments = models.TextField(blank=True, null=True)
    submission_file = models.FileField(upload_to='submitted_assignments/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission for {self.assignment.title} at {self.submitted_at}"
