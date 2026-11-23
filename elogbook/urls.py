from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from elogbook.apps.accounts.views import home
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import HttpResponse

# Add a test view for WebSocket debugging
def websocket_test(request, user_id):
    return HttpResponse(f"WebSocket test endpoint for user {user_id}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('elogbook.apps.accounts.urls')),
    path('supervision/', include('elogbook.apps.supervision.urls')),
    path('notifications/', include('elogbook.apps.notifications.urls')),
    path('', home, name='home'),
    path('logbook/', include('elogbook.apps.logbook.urls')),
    path('assignments/', include('elogbook.apps.assignments.urls')),
    path('reports/', include('elogbook.apps.reports.urls')),
    
    # API endpoints (temporarily commented out to fix CSRF issues)
    # path('api/', include('elogbook.apps.api.urls')),
    
    path('', RedirectView.as_view(url='/accounts/dashboard/', permanent=False)),
    
    # Add a test HTTP route to check if WebSocket pattern works
    path('ws/chat/<int:user_id>/', websocket_test, name='websocket_test'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)