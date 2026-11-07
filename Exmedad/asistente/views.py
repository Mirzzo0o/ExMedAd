from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .services import consultar_asistente_ia

MAX_CARACTERES_PREGUNTA = 1000


@login_required
def asistente_view(request):
    respuesta_ia = None
    pregunta = ""

    if request.method == 'POST':
        pregunta = request.POST.get('pregunta', '').strip()[:MAX_CARACTERES_PREGUNTA]
        if pregunta:
            respuesta_ia = consultar_asistente_ia(pregunta)

    return render(request, 'asistente/asistente.html', {'respuesta': respuesta_ia, 'pregunta': pregunta})