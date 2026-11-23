from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Supervisor, Intern
from elogbook.apps.institutions.models import Institution, Department
from .models import SubmittedAssignment
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 20
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('role', 'phone_number', 'profile_picture', 'is_verified')
        }),
    )


@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'staff_id', 'position')
    list_filter = ('department', 'department__institution')
    search_fields = ('user__first_name', 'user__last_name', 'staff_id', 'department__name')
    list_per_page = 20
    # Use model references instead of strings
    autocomplete_fields = ['user', 'department']


@admin.register(Intern)
class InternAdmin(admin.ModelAdmin):
    list_display = ('user', 'registration_number', 'university', 'course_name', 'year_of_study', 'supervisor')
    list_filter = ('university', 'course_name', 'year_of_study', 'supervisor')
    search_fields = ('user__first_name', 'user__last_name', 'registration_number', 'course_name')
    list_per_page = 20
    # Use model references instead of strings
    autocomplete_fields = ['user', 'university', 'supervisor']


admin.site.register(SubmittedAssignment)