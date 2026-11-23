from django.urls import path, include

app_name = 'api'

urlpatterns = [
    # Logbook and intern-related API endpoints
    path('logbook/', include('elogbook.apps.logbook.api_urls')),
    
    # Supervision-related API endpoints
    path('supervision/', include('elogbook.apps.supervision.api_urls')),
]
