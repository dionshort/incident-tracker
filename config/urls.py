from django.contrib import admin
from django.urls import include, path

from incidents.urls import router

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("incidents.urls")),
    path('api-auth/', include("rest_framework.urls")),
]
