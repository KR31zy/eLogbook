from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('generate/', views.generate_report, name='generate_report'),
    path('<int:report_id>/edit/', views.edit_report, name='edit_report'),
    path('<int:report_id>/preview/', views.preview_report, name='preview_report'),
    path('<int:report_id>/signature/', views.add_signature, name='add_signature'),
    path('<int:report_id>/export/', views.export_pdf, name='export_pdf'),
]