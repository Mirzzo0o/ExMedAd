from django.shortcuts import render

def asistente_view(request):
    return render(request, 'asistente/asistente.html')
