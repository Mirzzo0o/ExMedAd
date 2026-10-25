from django.urls import path
from . import views

urlpatterns = [
    path('', views.examen_view, name='ver_examen'),
]