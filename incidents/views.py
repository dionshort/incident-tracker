from rest_framework import viewsets

from .models import Incident
from .serializers import IncidentSerializer


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)