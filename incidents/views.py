from rest_framework import viewsets

from .models import Incident
from .serializers import IncidentSerializer


class IncidentViewSet(viewsets.ModelViewSet):
    serializer_class = IncidentSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Incident.objects.all()
        return Incident.objects.filter(reporter=user)
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)