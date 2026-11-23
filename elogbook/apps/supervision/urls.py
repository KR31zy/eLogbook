from django.urls import path
from . import views

app_name = "supervision"

urlpatterns = [
    path("", views.SupervisorDashboardView.as_view(), name="dashboard"),

    # Logbooks
    path("logbooks/", views.LogbookListView.as_view(), name="logbooks"),
    path("logbooks/<int:pk>/review/", views.LogbookReviewView.as_view(), name="logbooks-review"),

    # Assignments
    path("assignments/", views.AssignmentListView.as_view(), name="assignments"),
    path("assignments/new/", views.AssignmentCreateView.as_view(), name="assignments-new"),
    path("assignments/<int:pk>/review/", views.AssignmentReviewView.as_view(), name="assignments-review"),
]
