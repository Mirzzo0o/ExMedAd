from django.urls import path
from . import views

urlpatterns = [
    path('', views.asistente_view, name='ver_asistente'),
]