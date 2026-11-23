from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import StudentLogbook, VirtualLogbook, WeeklyLogbookEntry
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=StudentLogbook)
def handle_logbook_approval(sender, instance, created, **kwargs):
    """
    Signal handler to create WeeklyLogbookEntry when a StudentLogbook is approved or rejected.
    """
    if not created and hasattr(instance.student, 'intern_profile'):
        intern = instance.student.intern_profile
        virtual_logbook, vl_created = VirtualLogbook.objects.get_or_create(intern=intern)
        
        logger.info(f"Processing logbook {instance.id} for intern {intern.user.username}")
        
        if instance.status == 'approved':
            week_number = virtual_logbook.get_next_week_number()
            logger.info(f"Creating approved weekly entry for week {week_number}")
            
            # Always create a new weekly entry for approved logbooks
            weekly_entry = WeeklyLogbookEntry.objects.create(
                virtual_logbook=virtual_logbook,
                week_number=week_number,
                student_logbook=instance,
                is_approved=True,
                approved_at=timezone.now(),
                approved_by=instance.supervisor,  # Set the supervisor who approved it
                supervisor_feedback=getattr(instance, 'supervisor_feedback', '') or ''  # Copy feedback to individual entry
            )
            logger.info(f"Created weekly entry {weekly_entry.id} for week {week_number}")
            
        elif instance.status == 'rejected':
            week_number = virtual_logbook.get_next_week_number()
            logger.info(f"Creating rejected weekly entry for week {week_number}")
            
            # Always create a new weekly entry for rejected logbooks
            weekly_entry = WeeklyLogbookEntry.objects.create(
                virtual_logbook=virtual_logbook,
                week_number=week_number,
                student_logbook=instance,
                is_rejected=True,
                rejected_at=timezone.now(),
                rejected_by=instance.supervisor,  # Set the supervisor who rejected it
                supervisor_feedback=getattr(instance, 'supervisor_feedback', '') or ''  # Copy feedback to individual entry
            )
            logger.info(f"Created rejected weekly entry {weekly_entry.id} for week {week_number}")
