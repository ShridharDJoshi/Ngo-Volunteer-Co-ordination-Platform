from django.contrib import admin
from .models import Complaint, ComplaintStatusLog


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'submitted_by', 'linked_ngo', 'created_at']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['title', 'description', 'location', 'submitted_by__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ComplaintStatusLog)
class ComplaintStatusLogAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'old_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['complaint__title', 'note']
    readonly_fields = ['created_at']
