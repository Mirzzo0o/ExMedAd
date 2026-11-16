import os
import re
import json
import logging
import pypdf
from openai import OpenAI
from django.contrib import messages
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


def _limpiar_rango(rango, texto_pdf):
    rango = str(rango or "").strip()
    if not rango:
        return ""

    if re.search(r"no\s+(especificad|indicad|aplic|informad|disponible)|sin\s+rango|n/a", rango, re.IGNORECASE):
        return ""

    texto_normalizado = texto_pdf.replace(",", ".")
    for numero in re.findall(r"\d+(?:[.,]\d+)?", rango):
        if numero.replace(",", ".") not in texto_normalizado:
            return ""

    return rango[:200]


def _ajustar_semaforo(semaforo, nombre, valor_texto, rango_limpio):
    semaforo = _normalizar_semaforo(semaforo)
    nombre_lower = (nombre or "").lower()

    if not rango_limpio:
        return "amarillo" if semaforo == "rojo" else semaforo

    match_val = re.search(r"\d+(?:[.,]\d+)?", str(valor_texto or ""))
    numeros_rango = re.findall(r"\d+(?:[.,]\d+)?", rango_limpio)

    if match_val and len(numeros_rango) == 2 and "-" in rango_limpio:
        val = float(match_val.group(0).replace(",", "."))
        n1 = float(numeros_rango[0].replace(",", "."))
        n2 = float(numeros_rango[1].replace(",", "."))
        low, high = min(n1, n2), max(n1, n2)

        if val < low or val > high:
            if "hdl" in nombre_lower and val > high:
                return "verde"
            return "rojo"
        return "verde"

    return semaforo


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
            print(f"[ERROR EXAMS PDF] No se pudo leer el PDF: {e}")
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
            print("[ERROR EXAMS] Falta la variable de entorno GROQ_API_KEY")
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
                    "rango_referencia": "Rango normal copiado tal como aparece escrito en el examen (ej: '70 - 100 mg/dL'). Si el examen no muestra un rango para este parámetro, devuelve una cadena vacía. Nunca escribas 'No especificado' ni inventes rangos",
                    "semaforo": "verde si el valor está dentro del rango normal del examen o es un hallazgo sano/protector (como HDL alto); rojo si el valor está fuera del rango normal indicado en el examen (por encima del máximo o por debajo del mínimo) o si el informe indica algo grave o urgente; amarillo solo si el examen no trae rango fijo para ese parámetro y requiere observación (como LDL limítrofe)",
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
            campos_parametro = {f.name for f in ParametroExamen._meta.get_fields()}

            with transaction.atomic():
                nuevo_examen = ExamenHistorial.objects.create(
                    usuario=request.user,
                    titulo=datos_procesados.get("titulo") or "Examen Médico",
                    resumen_general=datos_procesados.get("resumen_general") or "Sin resumen"
                )

                for item in datos_procesados.get("parametros", []):
                    nombre_param = item.get("nombre") or "Hallazgo"
                    valor_param = item.get("valor") or "Sin dato"
                    rango_limpio = _limpiar_rango(item.get("rango_referencia"), texto_pdf)

                    datos_param = {
                        "examen": nuevo_examen,
                        "nombre_parametro": nombre_param,
                        "valor_obtenido": valor_param,
                        "estado_semaforo": _ajustar_semaforo(
                            item.get("semaforo"),
                            nombre_param,
                            valor_param,
                            rango_limpio,
                        ),
                        "explicacion_coloquial": item.get("explicacion") or "",
                    }
                    if "rango_referencia" in campos_parametro:
                        datos_param["rango_referencia"] = rango_limpio

                    ParametroExamen.objects.create(**datos_param)

            return redirect('detalle_examen', examen_id=nuevo_examen.id)

        except json.JSONDecodeError as e:
            print(f"[ERROR EXAMS JSON] La IA devolvió un JSON inválido: {e}")
            logger.error("La IA devolvió un JSON inválido: %s", e)
            return render(request, 'exams/subir_examen.html', {
                'error': 'No pude interpretar el resultado del examen. Por favor, inténtalo de nuevo.'
            })

        except Exception as e:
            print(f"[ERROR EXAMS] {type(e).__name__}: {e}")
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


@login_required
def eliminar_examen(request, examen_id):
    examen = get_object_or_404(ExamenHistorial, id=examen_id, usuario=request.user)

    if request.method == 'POST':
        examen.delete()
        messages.success(request, 'El examen se eliminó correctamente.')
        return redirect('historial_examenes')

    return render(request, 'exams/confirmar_eliminar.html', {'examen': examen})