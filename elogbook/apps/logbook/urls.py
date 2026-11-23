from django.urls import path
from . import views

app_name = 'logbook'

urlpatterns = [
    path('templates/', views.template_list, name='template_list'),  # Changed from logbook_template_list to template_list
    path('templates/upload/', views.upload_template, name='upload_template'),
    path('templates/download/<int:template_id>/', views.download_template, name='download_template'),
    path('edit/<int:template_id>/', views.edit_logbook, name='edit_logbook'),
    path('convert/<int:logbook_id>/', views.convert_to_pdf, name='convert_to_pdf'),
    path('submit/<int:logbook_id>/', views.submit_logbook, name='submit_logbook'),
    path('review/', views.review_logbooks, name='review_logbooks'),
    path('review/<int:logbook_id>/', views.review_logbook, name='review_logbook'),
    path('virtual-logbook/', views.virtual_logbook_view, name='virtual_logbook'),
    path('download-weekly-word/<int:entry_id>/', views.download_weekly_entry_word, name='download_weekly_word'),
    path('download-weekly-pdf/<int:entry_id>/', views.download_weekly_entry_pdf, name='download_weekly_pdf'),
    path('debug-weekly-entry/<int:entry_id>/', views.debug_weekly_entry, name='debug_weekly_entry'),
    path('resubmit/<int:logbook_id>/', views.resubmit_logbook, name='resubmit_logbook'),
    path('virtual-progress-api/', views.virtual_progress_api, name='virtual_progress_api'),
]