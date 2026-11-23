import json
from django.db import models
from django.utils import timezone
from django.conf import settings  

class AuditLog(models.Model):
    class ActionType(models.TextChoices):
        USER_CREATED = 'USER_CREATED', 'User Created'
        USER_UPDATED = 'USER_UPDATED', 'User Updated'
        USER_DELETED = 'USER_DELETED', 'User Deleted'
        INSTITUTION_CREATED = 'INSTITUTION_CREATED', 'Institution Created'
        INSTITUTION_UPDATED = 'INSTITUTION_UPDATED', 'Institution Updated'
        INSTITUTION_DELETED = 'INSTITUTION_DELETED', 'Institution Deleted'
        DEPARTMENT_CREATED = 'DEPARTMENT_CREATED', 'Department Created'
        DEPARTMENT_UPDATED = 'DEPARTMENT_UPDATED', 'Department Updated'
        DEPARTMENT_DELETED = 'DEPARTMENT_DELETED', 'Department Deleted'
        LOGIN = 'LOGIN', 'User Login'
        LOGOUT = 'LOGOUT', 'User Logout'
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Password Changed'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ActionType.choices)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"