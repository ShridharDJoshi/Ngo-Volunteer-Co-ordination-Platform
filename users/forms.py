from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from ngos.models import VolunteerProfile, NGOProfile


class CustomUserRegistrationForm(UserCreationForm):
    """Registration form with role selection"""
    
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=[('VOLUNTEER', 'Volunteer'), ('NGO', 'NGO')])
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
            # Create corresponding profile
            if user.role == 'VOLUNTEER':
                VolunteerProfile.objects.create(user=user)
            elif user.role == 'NGO':
                NGOProfile.objects.create(
                    user=user,
                    organization_name=user.username
                )
        
        return user


class VolunteerProfileForm(forms.ModelForm):
    """Form for volunteer profile editing"""
    
    class Meta:
        model = VolunteerProfile
        fields = ['profile_photo', 'phone', 'address', 'skills', 'bio']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your address'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List your skills (e.g., Cleaning, Waste Management)'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class NGOProfileForm(forms.ModelForm):
    """Form for NGO profile editing"""
    
    class Meta:
        model = NGOProfile
        fields = ['logo', 'organization_name', 'phone', 'address', 'mission', 'description']
        widgets = {
            'organization_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Organization address'}),
            'mission': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Organization mission statement'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your organization'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
