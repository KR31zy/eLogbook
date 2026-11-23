from django import forms
from .models import LogbookTemplate, StudentLogbook

class LogbookTemplateForm(forms.ModelForm):
    class Meta:
        model = LogbookTemplate
        fields = ['name', 'description', 'word_file', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter template name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'word_file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Template Name',
            'description': 'Description',
            'word_file': 'Word Document',
            'is_active': 'Active Template',
        }

class StudentLogbookForm(forms.ModelForm):
    class Meta:
        model = StudentLogbook
        fields = ['supervisor', 'template', 'word_file', 'status', 'supervisor_feedback']
        widgets = {
            'supervisor': forms.Select(attrs={'class': 'form-control'}),
            'template': forms.Select(attrs={'class': 'form-control'}),
            'word_file': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'supervisor_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter feedback here...'}),
        }
        labels = {
            'supervisor': 'Supervisor',
            'template': 'Logbook Template',
            'word_file': 'Upload Logbook',
            'status': 'Status',
            'supervisor_feedback': 'Supervisor Feedback',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit supervisor choices to staff users only
        self.fields['supervisor'].queryset = self.fields['supervisor'].queryset.filter(is_staff=True)