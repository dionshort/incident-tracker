from django.contrib import admin
from django.urls import include, path

from incidents.views import health

from tracker_mcp import tools  # noqa: F401 (imported so the tools register)
from tracker_mcp.server import server

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('incidents.urls')),
    path('api-auth/', include("rest_framework.urls")),
    path('health/', health, name="health"),
    path("mcp/", server),
]
