import pypdf
import json
from openai import OpenAI
from django.shortcuts import render, redirect, get_object_or_404
from .models import ExamenHistorial, ParametroExamen

# Inicializamos el cliente apuntando a Groq con tu API Key de Groq
client = OpenAI(
    api_key="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",  # Reemplaza con tu clave que empieza por gsk_
    base_url="https://api.groq.com/openai/v1"
)

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
        Eres un asistente médico amigable para adultos mayores. Analiza el siguiente texto extraído de un examen médico (puede ser de laboratorio con números o un informe descriptivo como imagenología/biopsia):
        ---
        {texto_pdf}
        ---
        Necesito que identifiques los puntos clave, hallazgos o parámetros principales y devuelvas un objeto JSON válido con esta estructura exacta:
        {{
            "titulo": "Nombre del examen o estudio",
            "resumen_general": "Un resumen corto y muy sencillo para que un adulto mayor entienda el resultado global",
            "parametros": [
                {{
                    "nombre": "Nombre del hallazgo o parámetro (ej: 'Hígado', 'Glicemia' o 'Conclusión general')",
                    "valor": "Descripción del estado o valor (ej: 'Normal', '110 mg/dL' o 'Sin lesiones focales')",
                    "semaforo": "verde (si está normal o sano), amarillo (si hay algo leve a observar) o rojo (si requiere atención médica rápida)",
                    "explicacion": "Explicación muy sencilla y coloquial de lo que significa este resultado"
                }}
            ]
        }}
        """

        try:
            # Llamada a la API ultrarrápida de Groq
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Eres un asistente médico experto que responde estrictamente en formato JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            texto_respuesta = response.choices[0].message.content
            datos_procesados = json.loads(texto_respuesta)

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
            print(f"Error al conectar con Groq: {e}")
            return render(request, 'exams/subir_examen.html', {'error': 'No se pudo procesar el examen con Groq.'})

    return render(request, 'exams/subir_examen.html')

def historial_examenes(request):
    examenes = ExamenHistorial.objects.all().order_by('-fecha')
    return render(request, 'exams/historial.html', {'examenes': examenes})

def detalle_examen(request, examen_id):
    examen = get_object_or_404(ExamenHistorial, id=examen_id)
    return render(request, 'exams/detalle_examen.html', {'examen': examen})
