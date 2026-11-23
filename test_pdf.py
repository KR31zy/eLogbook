#!/usr/bin/env python
"""
Test script to debug PDF generation issues
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elogbook.settings')
django.setup()

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO

def test_pdf_generation():
    """Test basic PDF generation"""
    print("Testing PDF generation...")
    
    # Test basic PDF generation
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph('Test PDF Document', styles['Title']))
    story.append(Spacer(1, 20))
    story.append(Paragraph('This is a test to verify PDF structure.', styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph('Testing multiple paragraphs and proper formatting.', styles['Normal']))
    
    doc.build(story)
    
    buffer.seek(0)
    pdf_data = buffer.read()
    
    print(f'PDF size: {len(pdf_data)} bytes')
    print(f'PDF header: {pdf_data[:20]}')
    print(f'PDF starts with %PDF: {pdf_data.startswith(b"%PDF")}')
    print(f'PDF ends with %%EOF: {pdf_data.endswith(b"%%EOF\\n") or pdf_data.endswith(b"%%EOF")}')
    print(f'PDF trailer present: {b"%%EOF" in pdf_data}')
    
    # Save test PDF to file
    with open('test_output.pdf', 'wb') as f:
        f.write(pdf_data)
    print("Test PDF saved as 'test_output.pdf'")
    
    return buffer

if __name__ == '__main__':
    test_pdf_generation()
