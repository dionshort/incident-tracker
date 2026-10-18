from django.contrib import admin

from .models import Incident

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": ["title", "description", "severity", "status", "owner"]
        }),
        ("Date information", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    )
    
    list_display = ["title", "severity", "status", "owner", "created_at", "updated_at"]
    list_filter = ["severity", "status"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]