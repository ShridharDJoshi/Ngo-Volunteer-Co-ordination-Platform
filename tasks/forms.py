from django import forms
from .models import Task, TaskCompletionProof
from ngos.models import Membership


class TaskAssignmentForm(forms.ModelForm):
    """Form for NGO to assign tasks to volunteers"""
    
    class Meta:
        model = Task
        fields = ['assigned_volunteer']
    
    def __init__(self, ngo_profile=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if ngo_profile:
            # Only show approved volunteers for this NGO
            approved_volunteers = Membership.objects.filter(
                ngo=ngo_profile,
                status='APPROVED'
            ).values_list('volunteer', flat=True)
            
            self.fields['assigned_volunteer'].queryset = self.fields['assigned_volunteer'].queryset.filter(
                id__in=approved_volunteers,
                role='VOLUNTEER'
            )
            self.fields['assigned_volunteer'].label = 'Assign to Volunteer'
            self.fields['assigned_volunteer'].empty_label = 'Select a volunteer'


class TaskCompletionProofForm(forms.ModelForm):
    """Form for volunteers to upload completion proof"""
    
    class Meta:
        model = TaskCompletionProof
        fields = ['image', 'description']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Describe the work completed (optional)'
            }),
        }
