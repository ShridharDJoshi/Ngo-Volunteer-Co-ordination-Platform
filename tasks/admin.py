from django.contrib import admin
from .models import Task, TaskCompletionProof


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'assigned_volunteer', 'status', 'assigned_at']
    list_filter = ['status', 'assigned_at']
    search_fields = ['complaint__title', 'assigned_volunteer__username']
    readonly_fields = ['assigned_at', 'accepted_at', 'completed_at', 'updated_at']


@admin.register(TaskCompletionProof)
class TaskCompletionProofAdmin(admin.ModelAdmin):
    list_display = ['task', 'uploaded_at']
    list_filter = ['uploaded_at']
    readonly_fields = ['uploaded_at']
