import os
import time
import logging
import httpx
from google import genai
from google.genai import types, errors

logger = logging.getLogger(__name__)

MENSAJE_SIN_CONEXION = (
    "Lo siento, en este momento no puedo conectarme para responderte. "
    "Por favor revisa tu conexión a internet e inténtalo de nuevo en unos minutos. "
    "Si es algo urgente sobre tu salud, comunícate directamente con tu médico o con un servicio de emergencia. 💙"
)

MENSAJE_ALTA_DEMANDA = (
    "El asistente está recibiendo muchas consultas simultáneas en este momento. "
    "Por favor, intenta presionar 'Preguntar' nuevamente en unos segundos. 💙"
)

MENSAJE_ERROR_GENERAL = (
    "Perdón, tuve un pequeño problema para responderte. "
    "¿Podrías intentarlo otra vez en un momento? "
    "Si es algo urgente sobre tu salud, consulta a tu médico. 💙"
)

MAX_INTENTOS = 2
# AQUÍ ESTÁ EL MODELO EXACTO QUE PIDE EL ERROR
MODELOS_DISPONIBLES = ['gemini-3.8-flash']

ERRORES_DE_RED = (
    ConnectionError,
    TimeoutError,
    OSError,
    httpx.ConnectError,
    httpx.TimeoutException,
    httpx.NetworkError,
)

def consultar_asistente_ia(pregunta_usuario: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR ExMedAd] GEMINI_API_KEY no encontrada en las variables de entorno.")
        return "Error: No se encontró la API Key de Gemini configurada en el servidor."

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[ERROR ExMedAd] Fallo al inicializar el cliente Gemini: {e}")
        return MENSAJE_ERROR_GENERAL

    configuracion_sistema = types.GenerateContentConfig(
        system_instruction=(
            "Eres el asistente virtual de ExMedAd, un compañero de apoyo para adultos mayores y sus cuidadores. "
            "Responde de forma clara, cálida, sencilla y con un lenguaje muy fácil de entender. "
            "IMPORTANTE: No des diagnósticos definitivos ni recetes medicamentos; siempre recuerda consultar a un médico profesional ante dudas graves."
        ),
        temperature=0.7,
    )

    for nombre_modelo in MODELOS_DISPONIBLES:
        for intento in range(1, MAX_INTENTOS + 1):
            try:
                response = client.models.generate_content(
                    model=nombre_modelo,
                    contents=pregunta_usuario,
                    config=configuracion_sistema,
                )

                if response and response.text:
                    return response.text

            except ERRORES_DE_RED as e:
                print(f"[ERROR RED] Modelo {nombre_modelo} Intento {intento}: {e}")
                if intento == MAX_INTENTOS and nombre_modelo == MODELOS_DISPONIBLES[-1]:
                    return MENSAJE_SIN_CONEXION
                time.sleep(1)

            except errors.APIError as e:
                codigo = getattr(e, "code", None)
                print(f"[ERROR API GEMINI] Modelo {nombre_modelo} Intento {intento}: {e}")
                # Manejar 429 (Too Many Requests) o 503 (Service Unavailable)
                if codigo in (429, 503):
                    if intento == MAX_INTENTOS and nombre_modelo == MODELOS_DISPONIBLES[-1]:
                        return MENSAJE_ALTA_DEMANDA
                    time.sleep(1)
                    continue # Reintenta si quedan intentos
                break # Si es otro error de API, sale del loop de intentos

            except Exception as e:
                print(f"[ERROR INESPERADO]: {e}")
                break

    return MENSAJE_ALTA_DEMANDA