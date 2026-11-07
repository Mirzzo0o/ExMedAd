import os
import json
import logging
import pypdf
from openai import OpenAI
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .models import ExamenHistorial, ParametroExamen

logger = logging.getLogger(__name__)

MAX_CARACTERES_PDF = 20000


def _obtener_cliente():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")


def _normalizar_semaforo(valor):
    valor = (valor or "").lower()
    for color in ("verde", "amarillo", "rojo"):
        if color in valor:
            return color
    return "amarillo"


@login_required
def subir_examen(request):
    if request.method == 'POST' and request.FILES.get('archivo_pdf'):
        pdf_file = request.FILES['archivo_pdf']

        texto_pdf = ""
        try:
            lector = pypdf.PdfReader(pdf_file)
            for pagina in lector.pages:
                texto_pdf += pagina.extract_text() or ""
        except Exception as e:
            logger.warning("No se pudo leer el PDF: %s", e)
            return render(request, 'exams/subir_examen.html', {
                'error': 'No pude leer el PDF. Revisa que sea un archivo válido e inténtalo de nuevo.'
            })

        if not texto_pdf.strip():
            return render(request, 'exams/subir_examen.html', {
                'error': 'El PDF no tiene texto legible. Si es una foto o un escaneo, todavía no puedo leerlo.'
            })

        texto_pdf = texto_pdf[:MAX_CARACTERES_PDF]

        client = _obtener_cliente()
        if client is None:
            logger.error("Falta la variable de entorno GROQ_API_KEY")
            return render(request, 'exams/subir_examen.html', {
                'error': 'El servicio de análisis no está disponible en este momento. Inténtalo más tarde.'
            })

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
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Eres un asistente médico experto que responde estrictamente en formato JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            datos_procesados = json.loads(response.choices[0].message.content)

            with transaction.atomic():
                nuevo_examen = ExamenHistorial.objects.create(
                    usuario=request.user,
                    titulo=datos_procesados.get("titulo") or "Examen Médico",
                    resumen_general=datos_procesados.get("resumen_general") or "Sin resumen"
                )

                for item in datos_procesados.get("parametros", []):
                    ParametroExamen.objects.create(
                        examen=nuevo_examen,
                        nombre_parametro=item.get("nombre") or "Hallazgo",
                        valor_obtenido=item.get("valor") or "Sin dato",
                        estado_semaforo=_normalizar_semaforo(item.get("semaforo")),
                        explicacion_coloquial=item.get("explicacion") or ""
                    )

            return redirect('detalle_examen', examen_id=nuevo_examen.id)

        except json.JSONDecodeError as e:
            logger.error("La IA devolvió un JSON inválido: %s", e)
            return render(request, 'exams/subir_examen.html', {
                'error': 'No pude interpretar el resultado del examen. Por favor, inténtalo de nuevo.'
            })

        except Exception as e:
            logger.exception("Error al procesar el examen: %s", e)
            return render(request, 'exams/subir_examen.html', {
                'error': 'No se pudo procesar el examen en este momento. Revisa tu conexión a internet e inténtalo de nuevo en unos minutos.'
            })

    return render(request, 'exams/subir_examen.html')


@login_required
def historial_examenes(request):
    examenes = ExamenHistorial.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'exams/historial.html', {'examenes': examenes})


@login_required
def detalle_examen(request, examen_id):
    examen = get_object_or_404(ExamenHistorial, id=examen_id, usuario=request.user)
    return render(request, 'exams/detalle_examen.html', {'examen': examen})
