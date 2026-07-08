from django import forms
from .models import Complaint, ComplaintHelpRequest
from ngos.models import NGOProfile, Membership


class ComplaintForm(forms.ModelForm):
    """Form for submitting complaints"""
    
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'location', 'category', 'image', 'linked_ngo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'placeholder': 'Enter the location of the issue', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'linked_ngo': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make linked_ngo optional for all users
        self.fields['linked_ngo'].required = False
        self.fields['linked_ngo'].label = 'Preferred NGO (Optional)'
        self.fields['linked_ngo'].help_text = 'Leave blank to make complaint visible to all NGOs'
        
        if user and user.is_volunteer():
            # Show only verified NGOs that the volunteer is a member of
            approved_memberships = Membership.objects.filter(
                volunteer=user,
                status='APPROVED',
                ngo__is_verified=True
            ).values_list('ngo', flat=True)
            self.fields['linked_ngo'].queryset = NGOProfile.objects.filter(id__in=approved_memberships)
        else:
            # For non-members, show only verified NGOs
            self.fields['linked_ngo'].queryset = NGOProfile.objects.filter(is_verified=True)


class HelpRequestForm(forms.ModelForm):
    """Form for NGO to request volunteer help"""
    
    class Meta:
        model = ComplaintHelpRequest
        fields = ['volunteer', 'message']
        widgets = {
            'volunteer': forms.Select(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Explain what help you need...'}),
        }
    
    def __init__(self, ngo_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if ngo_user and ngo_user.is_ngo():
            # Show only approved volunteers for this NGO
            approved_volunteers = Membership.objects.filter(
                ngo__user=ngo_user,
                status='APPROVED'
            ).values_list('volunteer', flat=True)
            
            from users.models import CustomUser
            self.fields['volunteer'].queryset = CustomUser.objects.filter(id__in=approved_volunteers)
            self.fields['volunteer'].label = 'Select Volunteer'
