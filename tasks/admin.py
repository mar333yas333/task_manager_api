from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Task

class TaskAdmin(admin.ModelAdmin):
    """
    Admin interface for Task model.
    """
    list_display = ('title', 'user', 'priority', 'status', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'due_date')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description')
        }),
        ('Task Details', {
            'fields': ('priority', 'status', 'due_date', 'due_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

# Register models
admin.site.register(Task, TaskAdmin)