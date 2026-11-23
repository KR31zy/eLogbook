from django.core.management.base import BaseCommand
from elogbook.apps.logbook.models import WeeklyLogbookEntry, StudentLogbook


class Command(BaseCommand):
    help = 'Test virtual logbook functionality after supervisor_feedback field addition'

    def handle(self, *args, **options):
        self.stdout.write("Testing Virtual Logbook functionality...")
        
        # Check if supervisor_feedback field exists
        try:
            field = WeeklyLogbookEntry._meta.get_field('supervisor_feedback')
            self.stdout.write(self.style.SUCCESS(f"✓ supervisor_feedback field exists: {field}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ supervisor_feedback field missing: {e}"))
            return
        
        # Check student_logbook field type
        try:
            field = WeeklyLogbookEntry._meta.get_field('student_logbook')
            self.stdout.write(self.style.SUCCESS(f"✓ student_logbook field type: {field.__class__.__name__}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error checking student_logbook field: {e}"))
            return
        
        # Check if we can query weekly entries
        try:
            entries = WeeklyLogbookEntry.objects.all()
            self.stdout.write(self.style.SUCCESS(f"✓ Can query WeeklyLogbookEntry objects: {entries.count()} entries found"))
            
            # Display sample entries
            for entry in entries[:3]:
                status = 'Approved' if entry.is_approved else 'Rejected' if entry.is_rejected else 'Pending'
                self.stdout.write(f"  - Week {entry.week_number}: {status}")
                if entry.supervisor_feedback:
                    feedback_preview = entry.supervisor_feedback[:50] + "..." if len(entry.supervisor_feedback) > 50 else entry.supervisor_feedback
                    self.stdout.write(f"    Feedback: {feedback_preview}")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error querying WeeklyLogbookEntry: {e}"))
            return
        
        # Test related name
        try:
            logbook = StudentLogbook.objects.first()
            if logbook and hasattr(logbook, 'weekly_entries'):
                weekly_entries_count = logbook.weekly_entries.count()
                self.stdout.write(self.style.SUCCESS(f"✓ Related name 'weekly_entries' works: {weekly_entries_count} entries"))
            else:
                self.stdout.write(self.style.WARNING("! No StudentLogbook found or related name not working"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error testing related name: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\n✓ Virtual Logbook functionality test completed!"))
