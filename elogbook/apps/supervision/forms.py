from django import forms
from django.contrib.auth import get_user_model
from elogbook.apps.assignments.models import Assignment
from elogbook.apps.accounts.models import Intern

User = get_user_model()


class AssignmentCreateForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'intern', 'deadline', 'assignment_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter assignment title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter assignment description'
            }),
            'intern': forms.Select(attrs={
                'class': 'form-select'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'assignment_file': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        supervisor = kwargs.pop('supervisor', None)
        super().__init__(*args, **kwargs)
        
        if supervisor:
            # Only show interns assigned to this supervisor
            self.fields['intern'].queryset = Intern.objects.filter(
                supervisor=supervisor
            ).select_related('user')
            
        # Update field labels and help text
        self.fields['intern'].label = 'Assign to Intern'
        self.fields['deadline'].label = 'Due Date'
        self.fields['assignment_file'].label = 'Assignment File (Optional)'
        self.fields['assignment_file'].help_text = 'Upload any supporting documents or templates'

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline:
            from django.utils import timezone
            if deadline <= timezone.now():
                raise forms.ValidationError("Deadline must be in the future.")
        return deadline
