from django.contrib import admin

from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": ["title", "description", "severity", "status", "assignee", "reporter"]
        }),
        ("Date information", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    )
    
    list_display = ["title", "severity", "status", "assignee", "reporter", "created_at", "updated_at"]
    list_filter = ["severity", "status", "assignee"]
    search_fields = ["title", "description"]
    readonly_fields = ["reporter", "created_at", "updated_at"]
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.reporter = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        return False