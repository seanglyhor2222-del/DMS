from django.contrib import admin
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'document', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'description')
