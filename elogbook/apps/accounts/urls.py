from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),                  
    path('login/', views.custom_login, name='login'), 
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-data/', views.dashboard_data, name='dashboard_data'),
    path('help/', views.help_center, name='help'),

    # Authentication helpers
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:home'), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change_form.html',
        success_url=reverse_lazy('accounts:password_change_done')
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
    path('delete/', views.delete_account, name='delete_account'),
    path('remove_picture/', views.remove_profile_picture, name='remove_profile_picture'),
    path('submitassignment/<int:pk>/', views.submitassignment, name='submitassignment'),  

]
