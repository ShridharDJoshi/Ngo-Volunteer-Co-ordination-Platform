from django.contrib import admin
from .models import VolunteerProfile, NGOProfile, Membership


@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    list_filter = ['created_at']


@admin.register(NGOProfile)
class NGOProfileAdmin(admin.ModelAdmin):
    list_display = ['organization_name', 'user', 'phone', 'is_verified', 'created_at']
    search_fields = ['organization_name', 'user__username', 'user__email']
    list_filter = ['created_at', 'is_verified']
    list_editable = ['is_verified']
    actions = ['verify_ngos', 'unverify_ngos']
    
    def verify_ngos(self, request, queryset):
        """Verify selected NGOs"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} NGO(s) successfully verified.')
    verify_ngos.short_description = 'Verify selected NGOs'
    
    def unverify_ngos(self, request, queryset):
        """Unverify selected NGOs"""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} NGO(s) unverified.')
    unverify_ngos.short_description = 'Unverify selected NGOs'


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['volunteer', 'ngo', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['volunteer__username', 'ngo__organization_name']
