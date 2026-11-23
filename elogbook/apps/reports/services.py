from datetime import datetime
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import slugify
from io import BytesIO
import os

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from elogbook.apps.logbook.models import VirtualLogbook


def build_simple_report_docx(intern_user) -> BytesIO:
    """Build a simple report DOCX from virtual logbook activities only."""
    doc = Document()
    
    # Set basic font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    # Title
    title = doc.add_heading('Internship Logbook Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Intern info
    doc.add_paragraph(f"Intern: {intern_user.get_full_name() or intern_user.username}")
    doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    doc.add_paragraph()

    # Get virtual logbook data
    try:
        intern_profile = getattr(intern_user, 'intern_profile', None)
        if intern_profile and hasattr(intern_profile, 'virtual_logbook'):
            v_log = intern_profile.virtual_logbook
            weeks = list(v_log.get_approved_weeks())
            if not weeks:
                weeks = list(v_log.get_all_weeks())
        else:
            weeks = []
    except:
        weeks = []

    if weeks:
        doc.add_heading('Weekly Activities', level=1)
        
        for week in weeks:
            doc.add_heading(f'Week {week.week_number}', level=2)
            
            # Add basic info about the week
            if hasattr(week, 'student_logbook') and week.student_logbook:
                doc.add_paragraph(f"Template: {week.student_logbook.template.name}")
                if week.student_logbook.supervisor_feedback:
                    doc.add_paragraph(f"Supervisor Feedback: {week.student_logbook.supervisor_feedback}")
            
            doc.add_paragraph()
    else:
        doc.add_heading('No Activities Found', level=1)
        doc.add_paragraph("No weekly logbook entries found for this intern.")

    # Return buffer
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output


def generate_simple_report_files(intern_user, fmt: str = 'pdf'):
    """Generate simple report files from virtual logbook."""
    docx_buffer = build_simple_report_docx(intern_user)
    base_name = slugify(f"Logbook_Report_{intern_user.username}_{datetime.now().strftime('%Y%m%d_%H%M')}")

    if fmt == 'docx':
        return f"{base_name}.docx", docx_buffer.getvalue()

    # Try PDF conversion
    try:
        import tempfile
        from docx2pdf import convert
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
            tmp_docx.write(docx_buffer.getvalue())
            tmp_docx_path = tmp_docx.name
            
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            tmp_pdf_path = tmp_pdf.name
            
        convert(tmp_docx_path, tmp_pdf_path)
        
        with open(tmp_pdf_path, 'rb') as f:
            pdf_bytes = f.read()
            
        os.unlink(tmp_docx_path)
        os.unlink(tmp_pdf_path)
        
        return f"{base_name}.pdf", pdf_bytes
        
    except Exception:
        # Fallback to DOCX if PDF conversion fails
        return f"{base_name}.docx", docx_buffer.getvalue()
