#!/usr/bin/env python
"""
Test script to verify virtual logbook functionality after supervisor_feedback field addition.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elogbook.settings')
django.setup()

from django.contrib.auth.models import User
from elogbook.apps.accounts.models import InternProfile, SupervisorProfile
from elogbook.apps.logbook.models import StudentLogbook, VirtualLogbook, WeeklyLogbookEntry, LogbookTemplate

def test_virtual_logbook():
    print("Testing Virtual Logbook functionality...")
    
    # Check if supervisor_feedback field exists in WeeklyLogbookEntry
    try:
        # Try to access the field through the model's _meta
        field = WeeklyLogbookEntry._meta.get_field('supervisor_feedback')
        print(f"✓ supervisor_feedback field exists: {field}")
    except Exception as e:
        print(f"✗ supervisor_feedback field missing: {e}")
        return False
    
    # Check if we can query weekly entries
    try:
        entries = WeeklyLogbookEntry.objects.all()
        print(f"✓ Can query WeeklyLogbookEntry objects: {entries.count()} entries found")
        
        # Check if any entries have supervisor feedback
        entries_with_feedback = entries.exclude(supervisor_feedback='')
        print(f"✓ Entries with supervisor feedback: {entries_with_feedback.count()}")
        
        # Display sample entries
        for entry in entries[:3]:
            print(f"  - Week {entry.week_number}: {'Approved' if entry.is_approved else 'Rejected' if entry.is_rejected else 'Pending'}")
            if entry.supervisor_feedback:
                print(f"    Feedback: {entry.supervisor_feedback[:50]}...")
            
    except Exception as e:
        print(f"✗ Error querying WeeklyLogbookEntry: {e}")
        return False
    
    # Test the ForeignKey relationship
    try:
        # Check if student_logbook is now a ForeignKey (allows multiple entries per logbook)
        field = WeeklyLogbookEntry._meta.get_field('student_logbook')
        print(f"✓ student_logbook field type: {field.__class__.__name__}")
        
        # Check related_name works
        if hasattr(StudentLogbook.objects.first(), 'weekly_entries'):
            print("✓ Related name 'weekly_entries' is accessible")
        else:
            print("✗ Related name 'weekly_entries' not accessible")
            
    except Exception as e:
        print(f"✗ Error checking student_logbook relationship: {e}")
        return False
    
    print("\n✓ Virtual Logbook functionality test completed successfully!")
    return True

if __name__ == "__main__":
    test_virtual_logbook()
