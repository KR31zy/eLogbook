from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
# Temporarily commented out due to dependency issues on Windows
# from weasyprint import HTML
from .models import Report, ReportSection
from .services import generate_simple_report_files
from elogbook.apps.logbook.models import StudentLogbook, VirtualLogbook, WeeklyLogbookEntry
from elogbook.apps.accounts.models import Intern

@login_required
def report_list(request):
    reports = Report.objects.filter(intern=request.user).order_by('-created_at')
    return render(request, 'reports/report_list.html', {
        'reports': reports
    })

@login_required
def generate_report(request):
    """Generate and return the PT report (DOCX or PDF) based on virtual logbook data.
    Requires 8 approved weekly entries.
    Usage: /reports/generate/?format=pdf|docx (default pdf)
    """
    try:
        intern_profile = Intern.objects.get(user=request.user)
        # Ensure virtual logbook exists for this intern
        v_log, _created = VirtualLogbook.objects.get_or_create(intern=intern_profile)
        # Generate from approved weeks if any; otherwise fall back to all weeks (user asked to enable anytime)
        # The services layer will handle assembling content gracefully.

        fmt = request.GET.get('format', 'pdf').lower()
        if fmt not in ('pdf', 'docx'):
            fmt = 'pdf'

        filename, file_bytes = generate_simple_report_files(request.user, fmt)
        response = HttpResponse(file_bytes, content_type=('application/pdf' if fmt == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Cache-Control'] = 'no-cache'
        return response

    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('accounts:dashboard')

@login_required
def edit_report(request, report_id):
    report = get_object_or_404(Report, id=report_id, intern=request.user)
    sections = report.sections.all().order_by('order')

    if request.method == 'POST':
        section_id = request.POST.get('section_id')
        content = request.POST.get('content')
        section = get_object_or_404(ReportSection, id=section_id, report=report)
        section.content = content
        section.save()
        messages.success(request, 'Section updated successfully.')
        return redirect('reports:edit_report', report_id=report.id)

    return render(request, 'reports/edit_report.html', {
        'report': report,
        'sections': sections
    })

@login_required
def preview_report(request, report_id):
    report = get_object_or_404(Report, id=report_id, intern=request.user)
    sections = report.sections.all().order_by('order')
    return render(request, 'reports/preview_report.html', {
        'report': report,
        'sections': sections
    })

@login_required
def add_signature(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST' and request.FILES.get('signature'):
        report.supervisor_signature = request.FILES['signature']
        report.status = 'signed'
        report.save()
        messages.success(request, 'Signature added successfully.')
    return redirect('reports:preview_report', report_id=report.id)

@login_required
def export_pdf(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    sections = report.sections.all().order_by('order')

    # Generate table of contents
    toc = []
    current_page = 1
    for section in sections:
        section.page_number = current_page
        section.save()
        toc.append({
            'title': section.title,
            'page': current_page
        })
        current_page += 1

    # Update report with TOC
    report.table_of_contents = {'sections': toc}
    report.save()
    
    # Temporarily disabled PDF generation due to weasyprint dependency issues on Windows
    messages.warning(request, 'PDF export is temporarily unavailable. Please try again later.')
    return redirect('reports:preview_report', report_id=report.id)
    
    # The following code is commented out due to weasyprint dependency issues
    '''
    # Render HTML template
    html_string = render_to_string('reports/pdf_template.html', {
        'report': report,
        'sections': sections,
        'toc': toc
    })

    # Generate PDF
    # html = HTML(string=html_string)
    # pdf = html.write_pdf()

    # Save PDF to report
    # report.status = 'exported'
    # report.generated_pdf.save(f'report_{report.id}.pdf', ContentFile(pdf))
    # report.save()

    # Serve PDF
    # response = HttpResponse(pdf, content_type='application/pdf')
    # response['Content-Disposition'] = f'attachment; filename="report_{report.id}.pdf"'
    '''
    
    # return response
