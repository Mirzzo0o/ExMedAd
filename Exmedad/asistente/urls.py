from django.urls import path
from .views import asistente_view

urlpatterns = [
    path('', asistente_view, name='asistente_chat'),
]
