from rest_framework import serializers

from .models import Incident


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ["id", "title", "description", "severity", "status", "reporter", "assignee", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]