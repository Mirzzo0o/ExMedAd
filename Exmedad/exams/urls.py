from django.urls import path
from . import views

urlpatterns = [
    path('subir/', views.subir_examen, name='subir_examen'),
    path('historial/', views.historial_examenes, name='historial_examenes'),
    path('detalle/<int:examen_id>/', views.detalle_examen, name='detalle_examen'),
]