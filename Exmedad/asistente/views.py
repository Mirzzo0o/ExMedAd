from django.shortcuts import render
from .services import consultar_asistente_ia

def asistente_view(request):
    respuesta_ia = None
    pregunta = ""
    
    if request.method == 'POST':
        pregunta = request.POST.get('pregunta', '')
        if pregunta:
            # Llamamos al servicio de IA que creamos para el asistente
            respuesta_ia = consultar_asistente_ia(pregunta)
            
    return render(request, 'asistente/asistente.html', {'respuesta': respuesta_ia, 'pregunta': pregunta})
