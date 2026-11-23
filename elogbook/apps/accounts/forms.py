from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, Supervisor, Intern, SubmittedAssignment
from elogbook.apps.institutions.models import Institution, Department
from PIL import Image


def validate_image(file):
    max_size = 2 * 1024 * 1024  # 2 MB
    if file.size > max_size:
        raise ValidationError('Image file too large (max 2MB).')


class UserSettingsForm(forms.ModelForm):
    # Keep profile_picture optional (we won't move upload UI to profile per user request)
    profile_picture = forms.ImageField(required=False, validators=[validate_image])

    class Meta:
        model = User
        # Keep fields to previous state (exclude notification toggles)
        fields = ['profile_picture', 'phone_number', 'theme']

    def save(self, commit=True):
        user = super().save(commit=False)

        # If a profile picture was uploaded, optionally resize it
        pic = self.cleaned_data.get('profile_picture')
        if pic:
            try:
                image = Image.open(pic)
                image.thumbnail((512, 512))
                # Save back to the InMemoryUploadedFile
                from io import BytesIO
                from django.core.files.uploadedfile import InMemoryUploadedFile
                buffer = BytesIO()
                image_format = image.format if image.format else 'PNG'
                image.save(buffer, format=image_format)
                buffer.seek(0)
                file_obj = InMemoryUploadedFile(buffer, 'ImageField', pic.name, pic.content_type, buffer.getbuffer().nbytes, None)
                user.profile_picture = file_obj
            except Exception:
                # If Pillow fails for some reason, keep the original file
                user.profile_picture = pic

        if commit:
            user.save()

        return user

class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = SubmittedAssignment
        fields = ['submission_file', 'comments']

# Enhanced User Management Forms

class CustomUserCreationForm(UserCreationForm):
    """Enhanced user creation form with role selection and additional fields"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(choices=User.Role.choices, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # Add placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Enter username'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter email address'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter first name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Enter phone number (optional)'
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.role = self.cleaned_data['role']
        user.is_verified = True  # Auto-verify admin-created users
        
        if commit:
            user.save()
        return user

class SupervisorCreationForm(forms.ModelForm):
    """Form for creating supervisor profiles"""
    # User fields
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    
    class Meta:
        model = Supervisor
        fields = ['staff_id', 'department', 'position', 'bio']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # Special handling for textarea
        self.fields['bio'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Brief bio or description (optional)'
        })
        
        # Add placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Enter username'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter email address'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter first name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Enter phone number (optional)'
        self.fields['staff_id'].widget.attrs['placeholder'] = 'Enter staff ID'
        self.fields['position'].widget.attrs['placeholder'] = 'Enter position/title (optional)'
        
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
            
        # Check if username already exists
        username = cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise ValidationError('Username already exists.')
            
        # Check if email already exists
        email = cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Email already exists.')
            
        # Check if staff_id already exists
        staff_id = cleaned_data.get('staff_id')
        if staff_id and Supervisor.objects.filter(staff_id=staff_id).exists():
            raise ValidationError('Staff ID already exists.')
            
        return cleaned_data
        
    def save(self, commit=True):
        # Create user first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            phone_number=self.cleaned_data['phone_number'],
            role=User.Role.SUPERVISOR,
            is_verified=True
        )
        
        # Create supervisor profile
        supervisor = super().save(commit=False)
        supervisor.user = user
        
        if commit:
            supervisor.save()
            
        return supervisor
