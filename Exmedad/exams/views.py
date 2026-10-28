import pypdf
import json
import re
from google import genai
from google.genai import types
from django.shortcuts import render, redirect, get_object_or_404
from .models import ExamenHistorial, ParametroExamen

# Inicializamos el cliente moderno de Google GenAI con tu API Key
client = genai.Client(api_key="AQ.Ab8RN6KkA1_iuVC114iQ4wOVid58-MfBaucHLlvG6GbuxtmHnA")

def subir_examen(request):
    if request.method == 'POST' and request.FILES.get('archivo_pdf'):
        pdf_file = request.FILES['archivo_pdf']
        
        texto_pdf = ""
        try:
            lector = pypdf.PdfReader(pdf_file)
            for pagina in lector.pages:
                texto_pdf += pagina.extract_text() or ""
        except Exception:
            texto_pdf = "Error al leer el PDF"

        prompt = f"""
        Eres un asistente médico amigable para adultos mayores. Analiza el siguiente texto extraído de un examen médico:
        ---
        {texto_pdf}
        ---
        Necesito que identifiques los parámetros médicos principales y me devuelvas UNICAMENTE un objeto JSON válido (sin texto adicional ni bloques de markdown si es posible) con esta estructura exacta:
        {{
            "titulo": "Nombre del examen",
            "resumen_general": "Un resumen corto y muy sencillo para un adulto mayor",
            "parametros": [
                {{
                    "nombre": "Nombre del parámetro (ej: Glicemia)",
                    "valor": "Valor numérico con su unidad (ej: 110 mg/dL)",
                    "semaforo": "verde, amarillo o rojo",
                    "explicacion": "Explicación muy sencilla y coloquial de lo que significa este valor"
                }}
            ]
        }}
        """

        try:
            # Llamada al modelo utilizando la librería moderna
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt,
            )
            
            texto_respuesta = response.text
            
            # Buscamos automáticamente el bloque JSON delimitado por llaves para evitar errores de formato
            match_json = re.search(r'\{.*\}', texto_respuesta, re.DOTALL)
            
            if match_json:
                texto_limpio = match_json.group(0)
            else:
                texto_limpio = texto_respuesta.replace("```json", "").replace("```", "").strip()
            
            # Intentamos decodificar el JSON de manera segura
            try:
                datos_procesados = json.loads(texto_limpio)
            except json.JSONDecodeError:
                print(f"Error: La IA no devolvió un JSON válido. Respuesta recibida: {texto_respuesta}")
                return render(request, 'exams/subir_examen.html', {'error': 'El formato devuelto por la IA no fue válido. Inténtalo de nuevo.'})

            nuevo_examen = ExamenHistorial.objects.create(
                titulo=datos_procesados.get("titulo", "Examen Médico"),
                resumen_general=datos_procesados.get("resumen_general", "Sin resumen")
            )

            for item in datos_procesados.get("parametros", []):
                ParametroExamen.objects.create(
                    examen=nuevo_examen,
                    nombre_parametro=item.get("nombre"),
                    valor_obtenido=item.get("valor"),
                    estado_semaforo=item.get("semaforo"),
                    explicacion_coloquial=item.get("explicacion")
                )

            return redirect('detalle_examen', examen_id=nuevo_examen.id)

        except Exception as e:
            print(f"Error al conectar con la IA: {e}")
            return render(request, 'exams/subir_examen.html', {'error': 'No se pudo procesar el examen con la inteligencia artificial.'})

    return render(request, 'exams/subir_examen.html')

def historial_examenes(request):
    examenes = ExamenHistorial.objects.all().order_by('-fecha')
    return render(request, 'exams/historial.html', {'examenes': examenes})

def detalle_examen(request, examen_id):
    examen = get_object_or_404(ExamenHistorial, id=examen_id)
    return render(request, 'exams/detalle_examen.html', {'examen': examen})
