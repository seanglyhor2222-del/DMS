from django.db import models
from django.conf import settings

class Report(models.Model):
    REPORT_TYPES = (
        ('document', 'Document Report'),
        ('activity', 'Activity Report'),
        ('user', 'User Report'),
        ('approval', 'Approval Report'),
    )
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    data = models.JSONField(default=dict)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.created_at.date()}"
    
    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
