import os
import tempfile
import io
import subprocess
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from .models import LogbookTemplate, StudentLogbook, VirtualLogbook, WeeklyLogbookEntry
from .forms import LogbookTemplateForm, StudentLogbookForm
from docx import Document
from docx.shared import Inches

@login_required
def template_list(request):
    templates = LogbookTemplate.objects.filter(is_active=True)
    return render(request, 'logbook/template_list.html', {'templates': templates})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def upload_template(request):
    if request.method == 'POST':
        form = LogbookTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, 'Logbook template uploaded successfully!')
            return redirect('logbook:template_list')
    else:
        form = LogbookTemplateForm()
    return render(request, 'logbook/upload_template.html', {'form': form})

@login_required
def download_template(request, template_id):
    template = get_object_or_404(LogbookTemplate, id=template_id)
    if not template.word_file:
        messages.error(request, 'Template file not found.')
        return redirect('logbook:template_list')
    
    file_path = template.word_file.path
    if not os.path.exists(file_path):
        messages.error(request, 'Template file not found on server.')
        return redirect('logbook:template_list')
        
    with open(file_path, 'rb') as file:
        response = HttpResponse(
            file.read(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        filename = os.path.basename(template.word_file.name)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

@login_required
def edit_logbook(request, template_id):
    template = get_object_or_404(LogbookTemplate, id=template_id)
    student_logbook, created = StudentLogbook.objects.get_or_create(
        student=request.user,
        template=template,
        defaults={'status': 'draft'}
    )

    if request.method == 'POST':
        if 'word_file' in request.FILES:
            student_logbook.word_file = request.FILES['word_file']
            student_logbook.status = 'draft'
            student_logbook.save()
            messages.success(request, 'Logbook updated successfully!')
            return redirect('logbook:edit_logbook', template_id=template_id)

    return render(request, 'logbook/edit_logbook.html', {
        'template': template,
        'student_logbook': student_logbook
    })

def convert_docx_to_pdf_simple(docx_path):
    """
    Simple PDF conversion using python-docx and reportlab for reliable output
    """
    try:
        # Method 1: Try using docx2pdf (simple and reliable)
        try:
            from docx2pdf import convert
            import tempfile
            import os
            from io import BytesIO
            
            # Create a temporary file for the PDF output
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf_path = temp_pdf.name
            
            # Convert using docx2pdf
            convert(docx_path, temp_pdf_path)
            
            # Validate the generated PDF file
            if os.path.exists(temp_pdf_path) and os.path.getsize(temp_pdf_path) > 100:
                # Read the PDF file into a buffer
                with open(temp_pdf_path, 'rb') as pdf_file:
                    pdf_content = BytesIO(pdf_file.read())
                
                # Clean up the temporary file
                os.unlink(temp_pdf_path)
                
                return pdf_content
            else:
                # Clean up and try next method
                if os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)
                raise Exception("docx2pdf generated invalid or empty PDF")
            
        except Exception as docx2pdf_error:
            print(f"docx2pdf conversion failed: {str(docx2pdf_error)}. Trying python-docx extraction...")
            
            # Method 2: Extract text from docx and create PDF with reportlab
            try:
                from docx import Document
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from io import BytesIO
                import re
                
                # Read the Word document
                doc = Document(docx_path)
                
                # Create PDF buffer
                buffer = BytesIO()
                pdf_doc = SimpleDocTemplate(buffer, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []
                
                # Extract and format content
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        # Clean up text
                        text = paragraph.text.strip()
                        # Create paragraph with proper styling
                        p = Paragraph(text, styles['Normal'])
                        story.append(p)
                        story.append(Spacer(1, 12))
                
                # Ensure we have content, add default if empty
                if not story:
                    story.append(Paragraph("Document Content", styles['Heading1']))
                    story.append(Spacer(1, 12))
                    story.append(Paragraph("This document appears to be empty or could not be processed.", styles['Normal']))
                
                # Build PDF
                pdf_doc.build(story)
                buffer.seek(0)
                
                return buffer
                
            except Exception as docx_error:
                print(f"python-docx conversion failed: {str(docx_error)}. Creating basic PDF with document info...")
                
                # Method 3: Create a basic PDF with document information using reportlab platypus
                try:
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                    from reportlab.lib.styles import getSampleStyleSheet
                    from reportlab.lib.pagesizes import letter
                    from io import BytesIO
                    import os
                    from datetime import datetime
                    
                    buffer = BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=letter)
                    styles = getSampleStyleSheet()
                    story = []
                    
                    # Title
                    story.append(Paragraph("Internship Logbook Document", styles['Title']))
                    story.append(Spacer(1, 20))
                    
                    # Document info
                    story.append(Paragraph(f"Original Document: {os.path.basename(docx_path)}", styles['Normal']))
                    story.append(Spacer(1, 12))
                    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
                    story.append(Spacer(1, 20))
                    
                    # Note
                    story.append(Paragraph("Note: This is a converted version of the Word document.", styles['Normal']))
                    story.append(Spacer(1, 12))
                    story.append(Paragraph("For the complete formatted version, please download the original Word document from the system.", styles['Normal']))
                    
                    # Build PDF
                    doc.build(story)
                    buffer.seek(0)
                    
                    return buffer
                    
                except Exception as basic_pdf_error:
                    print(f"Basic PDF creation failed: {str(basic_pdf_error)}. Using final fallback...")
                    
                    # Final fallback: Create minimal PDF using platypus for proper structure
                    from reportlab.platypus import SimpleDocTemplate, Paragraph
                    from reportlab.lib.styles import getSampleStyleSheet
                    from reportlab.lib.pagesizes import letter
                    from io import BytesIO
                    import os
                    from datetime import datetime
                    
                    buffer = BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=letter)
                    styles = getSampleStyleSheet()
                    story = []
                    
                    story.append(Paragraph("Logbook Document", styles['Title']))
                    story.append(Paragraph(f"File: {os.path.basename(docx_path)}", styles['Normal']))
                    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
                    
                    doc.build(story)
                    buffer.seek(0)
                    return buffer
                    
    except Exception as e:
        # Final fallback: Create a simple PDF with proper structure
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.pagesizes import letter
        from io import BytesIO
        import os
        from datetime import datetime
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph("Internship Logbook", styles['Title']))
        story.append(Spacer(1, 20))
        
        # File info
        story.append(Paragraph(f"Original Document: {os.path.basename(docx_path)}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Note
        story.append(Paragraph("Note: This PDF contains the document reference.", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Please download the original Word document for full content.", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("The system was unable to create an exact PDF copy.", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Multiple conversion methods were attempted without success.", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
        
import os

@login_required
def convert_to_pdf(request, logbook_id):
    student_logbook = get_object_or_404(StudentLogbook, id=logbook_id, student=request.user)
    
    if not student_logbook.word_file:
        messages.error(request, 'Please upload your logbook document first!')
        return redirect('logbook:edit_logbook', template_id=student_logbook.template.id)
    
    try:
        # Generate PDF with enhanced debugging directly
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.pagesizes import letter
        from io import BytesIO
        import os
        from datetime import datetime
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        story.append(Paragraph(f"Internship Logbook Confirmation", styles['Title']))
        story.append(Spacer(1, 20))
        
        # Document info
        story.append(Paragraph(f"Template: {student_logbook.template.name}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Intern: {request.user.get_full_name() or request.user.username}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Direct Word to PDF conversion
        try:
            from docx2pdf import convert
            import tempfile
            import os
            
            # Create temporary PDF file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf_path = temp_pdf.name
            
            # Convert Word document directly to PDF
            convert(student_logbook.word_file.path, temp_pdf_path)
            
            # Read the converted PDF
            with open(temp_pdf_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
            
            # Clean up temporary file
            os.unlink(temp_pdf_path)
            
            # Return the converted PDF
            response = HttpResponse(pdf_data, content_type='application/pdf')
            filename = f"{student_logbook.template.name}_{request.user.username}_confirmation.pdf"
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            response['Content-Length'] = len(pdf_data)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
            
        except Exception as conversion_error:
            # Fallback 1: Use Microsoft Word COM on Windows if available
            try:
                import sys
                if sys.platform.startswith('win'):
                    import tempfile
                    import os
                    import win32com.client
                    import pythoncom
                    
                    # Create temporary output path
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                        com_pdf_path = temp_pdf.name
                    os.unlink(com_pdf_path)  # Word expects the file not to exist yet
                    
                    # Initialize COM
                    pythoncom.CoInitialize()
                    try:
                        word = win32com.client.Dispatch('Word.Application')
                        word.Visible = False
                        doc = word.Documents.Open(student_logbook.word_file.path)
                        # 17 corresponds to wdFormatPDF
                        doc.SaveAs(com_pdf_path, FileFormat=17)
                        doc.Close()
                        word.Quit()
                    finally:
                        pythoncom.CoUninitialize()
                    
                    # Read the converted PDF
                    with open(com_pdf_path, 'rb') as f:
                        pdf_data = f.read()
                    os.unlink(com_pdf_path)
                    
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    filename = f"{student_logbook.template.name}_{request.user.username}_confirmation.pdf"
                    response['Content-Disposition'] = f'inline; filename="{filename}"'
                    response['Content-Length'] = len(pdf_data)
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    return response
                else:
                    raise RuntimeError('COM automation not available on this OS')
            except Exception as com_error:
                # If both methods fail, surface a clear error in the PDF shell
                story.append(Paragraph("Direct PDF conversion failed", styles['Heading2']))
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"docx2pdf error: {str(conversion_error)}", styles['Normal']))
                story.append(Spacer(1, 8))
                story.append(Paragraph(f"Word COM error: {str(com_error)}", styles['Normal']))
                story.append(Spacer(1, 12))
                story.append(Paragraph("Please download the original Word document.", styles['Normal']))
        
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Original Word document: {os.path.basename(student_logbook.word_file.name)}", styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Status: Draft", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        pdf_data = buffer.read()
        
        # Create a PDF response with proper headers
        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = f"{student_logbook.template.name}_{request.user.username}_confirmation.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Content-Length'] = len(pdf_data)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
    except Exception as e:
        messages.error(request, f'PDF generation failed: {str(e)}')
        return redirect('logbook:edit_logbook', template_id=student_logbook.template.id)

@login_required
def submit_logbook(request, logbook_id):
    student_logbook = get_object_or_404(StudentLogbook, id=logbook_id, student=request.user)
    
    if not student_logbook.word_file:
        messages.error(request, 'Please upload your logbook document before submitting!')
        return redirect('logbook:edit_logbook', template_id=student_logbook.template.id)
    
    # Always regenerate PDF from the current Word file to ensure consistency
    try:
        word_file_path = student_logbook.word_file.path
        pdf_content = convert_docx_to_pdf_simple(word_file_path)
        pdf_filename = f'{student_logbook.template.name}_{request.user.username}_submitted.pdf'
        
        # Remove old PDF if it exists to ensure we use the latest Word file
        if student_logbook.pdf_file:
            student_logbook.pdf_file.delete(save=False)
        
        student_logbook.pdf_file.save(pdf_filename, pdf_content)
        messages.success(request, 'PDF confirmation generated successfully!')
    except Exception as e:
        messages.warning(request, f'PDF conversion failed, but submission continued: {str(e)}')
    
    student_logbook.status = 'submitted'
    student_logbook.submitted_at = timezone.now()
    student_logbook.save()
    
    messages.success(request, 'Logbook submitted successfully for review!')
    return redirect('accounts:dashboard')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser or hasattr(u, 'supervisor_profile'))
def review_logbooks(request):
    logbooks = StudentLogbook.objects.filter(status='submitted')
    return render(request, 'logbook/review_list.html', {'logbooks': logbooks})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser or hasattr(u, 'supervisor_profile'))
def review_logbook(request, logbook_id):
    logbook = get_object_or_404(StudentLogbook, id=logbook_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        feedback = request.POST.get('feedback', '')
        
        if action == 'approve':
            logbook.status = 'approved'
            logbook.supervisor_feedback = feedback
            logbook.supervisor = request.user  # Set the supervisor who approved it
            messages.success(request, 'Logbook approved successfully!')
        elif action == 'reject':
            logbook.status = 'changes_requested'
            logbook.supervisor_feedback = feedback
            logbook.supervisor = request.user  # Set the supervisor who rejected it
            messages.success(request, 'Logbook returned for changes!')
        
        logbook.reviewed_at = timezone.now()
        logbook.save()
        
        return redirect('logbook:review_logbooks')
    
    return render(request, 'logbook/review_logbook.html', {'logbook': logbook})


@login_required
def virtual_logbook_view(request):
    """View for interns to see their virtual logbook progress"""
    if not hasattr(request.user, 'intern_profile'):
        messages.error(request, 'Access denied. Intern profile required.')
        return redirect('accounts:dashboard')
    
    intern = request.user.intern_profile
    virtual_logbook, created = VirtualLogbook.objects.get_or_create(intern=intern)
    
    # Get all weekly entries (approved and rejected)
    weekly_entries = virtual_logbook.get_all_weeks()
    
    context = {
        'virtual_logbook': virtual_logbook,
        'weekly_entries': weekly_entries,
        'total_weeks': weekly_entries.count(),
        'intern': intern
    }
    
    return render(request, 'logbook/virtual_logbook.html', context)


@login_required
def virtual_progress_api(request):
    """API endpoint for real-time virtual logbook progress updates"""
    if not hasattr(request.user, 'intern_profile'):
        return JsonResponse({'error': 'Not an intern'}, status=403)
    
    intern = request.user.intern_profile
    
    try:
        virtual_logbook = VirtualLogbook.objects.get(intern=intern)
        weekly_entries = virtual_logbook.weekly_entries.all()
        
        # Calculate progress statistics
        total_weeks = weekly_entries.filter(is_approved=True).count()
        approved_weeks = weekly_entries.filter(is_approved=True).count()
        pending_weeks = weekly_entries.filter(is_approved=False, is_rejected=False).count()
        revision_weeks = weekly_entries.filter(is_rejected=True).count()
        weeks_remaining = max(0, 8 - approved_weeks)
        progress_percent = int((approved_weeks / 8) * 100) if approved_weeks > 0 else 0
        
        return JsonResponse({
            'total_weeks': total_weeks,
            'approved_weeks': approved_weeks,
            'pending_weeks': pending_weeks,
            'revision_weeks': revision_weeks,
            'weeks_remaining': weeks_remaining,
            'progress_percent': progress_percent,
            'last_update': timezone.now().isoformat(),
            'status': 'success'
        })
        
    except VirtualLogbook.DoesNotExist:
        return JsonResponse({
            'total_weeks': 0,
            'approved_weeks': 0,
            'pending_weeks': 0,
            'revision_weeks': 0,
            'weeks_remaining': 8,
            'progress_percent': 0,
            'last_update': timezone.now().isoformat(),
            'status': 'no_logbook'
        })


@login_required
def download_weekly_entry_word(request, entry_id):
    """Download Word document for a specific weekly logbook entry (only for rejected entries)"""
    if not hasattr(request.user, 'intern_profile'):
        messages.error(request, 'Access denied. Intern profile required.')
        return redirect('accounts:dashboard')
    
    try:
        # Get the weekly entry and ensure it belongs to the current intern (only rejected entries can download Word)
        weekly_entry = WeeklyLogbookEntry.objects.select_related(
            'student_logbook', 'virtual_logbook__intern'
        ).get(
            id=entry_id,
            virtual_logbook__intern=request.user.intern_profile,
            is_rejected=True
        )
        
        student_logbook = weekly_entry.student_logbook
        
        if not student_logbook.word_file:
            messages.error(request, 'Word document not available for this entry.')
            return redirect('logbook:virtual_logbook')
        
        file_path = student_logbook.word_file.path
        if not os.path.exists(file_path):
            messages.error(request, 'Word document file not found on server.')
            return redirect('logbook:virtual_logbook')
        
        with open(file_path, 'rb') as file:
            response = HttpResponse(
                file.read(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            filename = f"Week_{weekly_entry.week_number}_{student_logbook.template.name}.docx"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
    except WeeklyLogbookEntry.DoesNotExist:
        messages.error(request, 'Weekly entry not found or access denied.')
        return redirect('logbook:virtual_logbook')
    except Exception as e:
        messages.error(request, f'Error downloading file: {str(e)}')
        return redirect('logbook:virtual_logbook')


@login_required
def download_weekly_entry_pdf(request, entry_id):
    """Download PDF document for a specific weekly logbook entry"""
    print(f"PDF DOWNLOAD - Entry ID: {entry_id}")
    
    if not hasattr(request.user, 'intern_profile'):
        messages.error(request, 'Access denied. Intern profile required.')
        return redirect('accounts:dashboard')
    
    try:
        weekly_entry = WeeklyLogbookEntry.objects.select_related(
            'student_logbook', 'virtual_logbook__intern'
        ).get(
            id=entry_id,
            virtual_logbook__intern=request.user.intern_profile,
            is_approved=True
        )
        
        student_logbook = weekly_entry.student_logbook
        
        if not student_logbook.word_file or not os.path.exists(student_logbook.word_file.path):
            messages.error(request, 'No Word document available for PDF conversion.')
            return redirect('logbook:virtual_logbook')
        
        word_file_path = student_logbook.word_file.path
        print(f"Converting: {word_file_path}")
        
        # Try docx2pdf conversion
        try:
            from docx2pdf import convert
            import tempfile
            
            print("Using docx2pdf...")
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf_path = temp_pdf.name
            
            convert(word_file_path, temp_pdf_path)
            
            with open(temp_pdf_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
            
            os.unlink(temp_pdf_path)
            print(f"SUCCESS: {len(pdf_data)} bytes")
            
            response = HttpResponse(pdf_data, content_type='application/pdf')
            filename = f"Week_{weekly_entry.week_number}_{student_logbook.template.name.replace(' ', '_')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(pdf_data)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            
            return response
            
        except Exception as e:
            # Fallback: serve the original Word document to avoid page reload with redirect
            print(f"PDF conversion failed, falling back to Word download: {str(e)}")
            try:
                from django.http import FileResponse
                fallback_filename = f"Week_{weekly_entry.week_number}_{student_logbook.template.name.replace(' ', '_')}.docx"
                docx_response = FileResponse(open(word_file_path, 'rb'),
                                             as_attachment=True,
                                             filename=fallback_filename,
                                             content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                # Cache-busting headers
                docx_response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                docx_response['Pragma'] = 'no-cache'
                docx_response['Expires'] = '0'
                return docx_response
            except Exception as fallback_err:
                print(f"Fallback Word download also failed: {str(fallback_err)}")
                messages.error(request, 'Download failed. Please try again or contact support.')
                return redirect('logbook:virtual_logbook')
        
    except WeeklyLogbookEntry.DoesNotExist:
        messages.error(request, 'Weekly entry not found or access denied.')
        return redirect('logbook:virtual_logbook')
    except Exception as e:
        print(f"ERROR: {str(e)}")
        messages.error(request, f'Download failed: {str(e)}')
        return redirect('logbook:virtual_logbook')


@login_required
def debug_weekly_entry(request, entry_id):
    """Debug view to check weekly entry details"""
    from django.http import JsonResponse
    
    try:
        entry = WeeklyLogbookEntry.objects.select_related(
            'student_logbook', 'virtual_logbook__intern'
        ).get(id=entry_id)
        
        data = {
            'entry_id': entry.id,
            'week_number': entry.week_number,
            'is_approved': entry.is_approved,
            'is_rejected': entry.is_rejected,
            'intern_user': entry.virtual_logbook.intern.user.username,
            'current_user': request.user.username,
            'has_intern_profile': hasattr(request.user, 'intern_profile'),
            'user_matches': hasattr(request.user, 'intern_profile') and entry.virtual_logbook.intern == request.user.intern_profile,
            'student_logbook_id': entry.student_logbook.id,
            'has_word_file': bool(entry.student_logbook.word_file),
            'word_file_name': entry.student_logbook.word_file.name if entry.student_logbook.word_file else None,
        }
        
        if entry.student_logbook.word_file:
            import os
            data['word_file_exists'] = os.path.exists(entry.student_logbook.word_file.path)
            data['word_file_path'] = entry.student_logbook.word_file.path
        
        return JsonResponse(data)
        
    except WeeklyLogbookEntry.DoesNotExist:
        return JsonResponse({'error': 'Weekly entry not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def resubmit_logbook(request, logbook_id):
    """Allow intern to re-edit and re-submit a rejected logbook"""
    if not hasattr(request.user, 'intern_profile'):
        messages.error(request, 'Access denied. Intern profile required.')
        return redirect('accounts:dashboard')
    
    try:
        # Get the logbook and ensure it belongs to the current intern
        logbook = StudentLogbook.objects.get(
            id=logbook_id,
            student=request.user,
            status='changes_requested'
        )
        
        if request.method == 'POST':
            form = StudentLogbookForm(request.POST, request.FILES, instance=logbook)
            if form.is_valid():
                # Reset status to pending for re-review
                logbook = form.save(commit=False)
                logbook.status = 'pending'
                logbook.supervisor_feedback = ''  # Clear previous feedback
                logbook.save()
                
                messages.success(request, f'Logbook re-submitted successfully for Week {logbook.weekly_entry.week_number}!')
                return redirect('logbook:virtual_logbook')
        else:
            form = StudentLogbookForm(instance=logbook)
        
        context = {
            'form': form,
            'logbook': logbook,
            'week_number': logbook.weekly_entry.week_number if hasattr(logbook, 'weekly_entry') else 'N/A'
        }
        
        return render(request, 'logbook/resubmit_logbook.html', context)
        
    except StudentLogbook.DoesNotExist:
        messages.error(request, 'Logbook not found or access denied.')
        return redirect('logbook:virtual_logbook')
    except Exception as e:
        messages.error(request, f'Error accessing logbook: {str(e)}')
        return redirect('logbook:virtual_logbook')