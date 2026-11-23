from django.urls import path
from . import api_views

app_name = 'logbook_api'

urlpatterns = [
    # Intern logbook endpoints
    path('submit/', api_views.submit_logbook, name='submit_logbook'),
    path('my-logbooks/', api_views.get_intern_logbooks, name='get_intern_logbooks'),
    
    # Intern assignment endpoints
    path('assignments/submit/', api_views.submit_assignment, name='submit_assignment'),
    path('assignments/my-assignments/', api_views.get_intern_assignments, name='get_intern_assignments'),
]
