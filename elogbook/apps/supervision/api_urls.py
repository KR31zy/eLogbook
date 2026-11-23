from django.urls import path
from . import api_views

app_name = 'supervision_api'

urlpatterns = [
    # Supervisor assignment endpoints
    path('assignments/create/', api_views.create_assignment, name='create_assignment'),
    path('assignments/my-assignments/', api_views.get_supervisor_assignments, name='get_supervisor_assignments'),
    
    # Review endpoints
    path('review/', api_views.review_submission, name='review_submission'),
    path('pending-submissions/', api_views.get_pending_submissions, name='get_pending_submissions'),
]
