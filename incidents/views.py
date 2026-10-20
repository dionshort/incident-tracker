from django.db import connection, DatabaseError
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

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


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
    except DatabaseError:
        return Response({"status": "unavailable"}, status=503)
    return Response({"status": "ok"})