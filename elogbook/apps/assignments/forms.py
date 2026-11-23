# assignments/forms.py
from django import forms
from .models import Assignment, AssignmentSubmission
from elogbook.apps.accounts.models import Intern


class AssignmentCreateForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'intern', 'deadline', 'assignment_file']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'assignment_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        supervisor = kwargs.pop('supervisor', None)
        super().__init__(*args, **kwargs)
        
        if supervisor:
            self.fields['intern'].queryset = supervisor.interns.all()
        else:
            self.fields['intern'].queryset = Intern.objects.all()
            
        self.fields['intern'].widget.attrs['class'] = 'form-control'
        self.fields['assignment_file'].required = False


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['submission_file', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Optional notes about your submission...'}),
            'submission_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.txt,.zip'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False


class AssignmentReviewForm(forms.ModelForm):
    REVIEW_CHOICES = [
        ('approved', 'Approve'),
        ('rejected', 'Request Revision'),
    ]
    
    review_decision = forms.ChoiceField(
        choices=REVIEW_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = AssignmentSubmission
        fields = ['supervisor_feedback']
        widgets = {
            'supervisor_feedback': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Provide feedback to the intern...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supervisor_feedback'].required = True