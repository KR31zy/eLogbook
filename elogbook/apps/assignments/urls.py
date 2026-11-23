# assignments/urls.py
from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    # Intern URLs
    path('my-assignments/', views.intern_assignments, name='intern_assignments'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    
    # Supervisor URLs
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/assignment/create/', views.create_assignment, name='create_assignment'),
    path('supervisor/assignment/<int:assignment_id>/update/', views.update_assignment, name='update_assignment'),
    path('supervisor/assignment/<int:assignment_id>/delete/', views.delete_assignment, name='delete_assignment'),
    path('supervisor/assignment/<int:assignment_id>/review/', views.review_submission, name='review_submission'),
    
    # File downloads
    path('assignment/<int:assignment_id>/download/', views.download_assignment_file, name='download_assignment_file'),
    path('assignment/<int:assignment_id>/download-submission/', views.download_submission_file, name='download_submission_file'),
]