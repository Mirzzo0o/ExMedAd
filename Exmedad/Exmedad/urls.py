from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('exams/', include('exams.urls')),
    path('asistente/', include('asistente.urls')),
]
