from django.shortcuts import render

def examen_view(request):
    return render(request, 'exams/examen.html')
