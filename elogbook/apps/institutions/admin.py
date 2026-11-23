from django.contrib import admin
from .models import Institution, Department

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'contact_phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'contact_email', 'contact_phone')
    list_per_page = 20


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'is_active', 'created_at')
    list_filter = ('institution', 'is_active', 'created_at')
    search_fields = ('name', 'institution__name')
    list_per_page = 20