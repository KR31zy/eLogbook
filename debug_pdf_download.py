#!/usr/bin/env python
"""
Debug script to identify PDF download issues in virtual logbook
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elogbook.settings')
django.setup()

from django.contrib.auth.models import User
from elogbook.apps.logbook.models import WeeklyLogbookEntry, StudentLogbook

def debug_pdf_download():
    print("Debugging PDF download functionality...")
    
    # Check if there are any weekly entries
    entries = WeeklyLogbookEntry.objects.all()
    print(f"Total weekly entries: {entries.count()}")
    
    if entries.count() == 0:
        print("❌ No weekly entries found - this is the main issue!")
        return
    
    # Check approved entries
    approved_entries = entries.filter(is_approved=True)
    print(f"Approved entries: {approved_entries.count()}")
    
    # Check each entry for PDF download requirements
    for entry in approved_entries[:5]:  # Check first 5
        print(f"\n--- Week {entry.week_number} (ID: {entry.id}) ---")
        print(f"Is approved: {entry.is_approved}")
        print(f"Student logbook ID: {entry.student_logbook.id}")
        print(f"Has word file: {bool(entry.student_logbook.word_file)}")
        
        if entry.student_logbook.word_file:
            print(f"Word file path: {entry.student_logbook.word_file.path}")
            print(f"File exists: {os.path.exists(entry.student_logbook.word_file.path)}")
        else:
            print("❌ No word file attached - PDF cannot be generated")
    
    # Check for missing dependencies
    try:
        from reportlab.platypus import SimpleDocTemplate
        print("✓ ReportLab available")
    except ImportError:
        print("❌ ReportLab not installed - PDF generation will fail")
    
    try:
        from docx import Document
        print("✓ python-docx available")
    except ImportError:
        print("❌ python-docx not installed - Word reading will fail")

if __name__ == "__main__":
    debug_pdf_download()
