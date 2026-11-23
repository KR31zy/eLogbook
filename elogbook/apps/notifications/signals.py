from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Message

@receiver(post_save, sender=Message)
def notify_new_message(sender, instance: Message, created: bool, **kwargs):
    """Email notify recipient on new message (best-effort)."""
    if not created:
        return
    try:
        recipient = instance.recipient
        subject = f"New message from {instance.sender.get_username()}"
        body = (
            f"You have received a new message on E-Logbook.\n\n"
            f"From: {instance.sender.get_username()}\n"
            f"Message:\n{instance.content}\n\n"
            f"Login to reply: {getattr(settings, 'SITE_URL', '')}/notifications/chat/{instance.sender.id}/"
        )
        if getattr(recipient, 'email', None):
            send_mail(
                subject,
                body,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
                [recipient.email],
                fail_silently=True,
            )
    except Exception:
        # Do not crash signal on email errors
        pass
