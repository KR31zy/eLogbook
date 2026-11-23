from django.core.management.base import BaseCommand
from elogbook.apps.logbook.models import WeeklyLogbookEntry, StudentLogbook
import os


class Command(BaseCommand):
    help = 'Check weekly entries and PDF download requirements'

    def handle(self, *args, **options):
        self.stdout.write("Checking weekly entries for PDF download...")
        
        # Check total entries
        total_entries = WeeklyLogbookEntry.objects.count()
        self.stdout.write(f"Total weekly entries: {total_entries}")
        
        if total_entries == 0:
            self.stdout.write(self.style.ERROR("❌ No weekly entries found!"))
            self.stdout.write("This means no logbooks have been approved yet.")
            return
        
        # Check approved entries
        approved_entries = WeeklyLogbookEntry.objects.filter(is_approved=True)
        self.stdout.write(f"Approved entries: {approved_entries.count()}")
        
        if approved_entries.count() == 0:
            self.stdout.write(self.style.WARNING("⚠️ No approved entries found!"))
            self.stdout.write("PDF downloads are only available for approved entries.")
            return
        
        # Check each approved entry
        for entry in approved_entries[:5]:
            self.stdout.write(f"\n--- Week {entry.week_number} (ID: {entry.id}) ---")
            self.stdout.write(f"Intern: {entry.virtual_logbook.intern.user.get_full_name()}")
            self.stdout.write(f"Is approved: {entry.is_approved}")
            
            student_logbook = entry.student_logbook
            self.stdout.write(f"Student logbook ID: {student_logbook.id}")
            self.stdout.write(f"Has word file: {bool(student_logbook.word_file)}")
            
            if student_logbook.word_file:
                file_path = student_logbook.word_file.path
                self.stdout.write(f"Word file: {student_logbook.word_file.name}")
                self.stdout.write(f"File path: {file_path}")
                self.stdout.write(f"File exists: {os.path.exists(file_path)}")
                
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    self.stdout.write(f"File size: {file_size} bytes")
                    self.stdout.write(self.style.SUCCESS("✓ PDF download should work"))
                else:
                    self.stdout.write(self.style.ERROR("❌ Word file missing - PDF cannot be generated"))
            else:
                self.stdout.write(self.style.ERROR("❌ No word file attached - PDF cannot be generated"))
        
        # Check dependencies
        try:
            from reportlab.platypus import SimpleDocTemplate
            self.stdout.write(self.style.SUCCESS("✓ ReportLab available"))
        except ImportError:
            self.stdout.write(self.style.ERROR("❌ ReportLab not installed"))
        
        try:
            from docx import Document
            self.stdout.write(self.style.SUCCESS("✓ python-docx available"))
        except ImportError:
            self.stdout.write(self.style.ERROR("❌ python-docx not installed"))
