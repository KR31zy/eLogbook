from django.db import models
from django.conf import settings
from django.utils import timezone

class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(  
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False) 
    read_at = models.DateTimeField(null=True, blank=True)  

    class Meta:
        ordering = ['-timestamp']  

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.content[:20]}"
    
    def mark_as_read(self):
        """Mark message as read with timestamp"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread messages for a user"""
        return cls.objects.filter(recipient=user, is_read=False).count()