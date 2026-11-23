
from django.urls import path
from . import views

app_name = "notifications" 

urlpatterns = [
    path('chat/', views.chat_view, name='chat'),
    path('chat/<int:user_id>/', views.chat_view, name='chat'),
    path('chat/<int:user_id>/send/', views.send_message, name='send_message'),
]
