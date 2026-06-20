from django.contrib import admin
from .models import Workflow, Approval

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'created_at')

@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'approver', 'status', 'created_at')
    list_filter = ('status', 'created_at')
