from django.contrib import admin
from .models import LogbookTemplate, StudentLogbook

@admin.register(LogbookTemplate)
class LogbookTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(StudentLogbook)
class StudentLogbookAdmin(admin.ModelAdmin):
    list_display = ['student', 'supervisor', 'template', 'status', 'submitted_at']
    list_filter = ['status', 'template', 'supervisor', 'submitted_at']
    search_fields = ['student__username', 'supervisor__username', 'template__name']
    readonly_fields = ['created_at', 'updated_at', 'submitted_at', 'reviewed_at']