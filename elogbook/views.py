# In elogbook/views.py (create this file if it doesn't exist)
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')