from django.conf import settings
from django.db import models

class Incident(models.Model):
    class Severity(models.TextChoices):
        LOW = 'low'
        MEDIUM = 'medium'
        HIGH = 'high'
        CRITICAL = 'critical'
    
    
    class Status(models.TextChoices):
        OPEN = 'open'
        INVESTIGATING = 'investigating'
        RESOLVED = 'resolved'
    
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL, related_name='incidents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    class Meta:
        ordering = ['-created_at']
    
    
    def __str__(self):
        return self.title