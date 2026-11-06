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

MENSAJE_ERROR_GENERAL = (
    "Perdón, tuve un pequeño problema para responderte. "
    "¿Podrías intentarlo otra vez en un momento? "
    "Si es algo urgente sobre tu salud, consulta a tu médico. 💙"
)

MAX_INTENTOS = 3
ESPERA_SEGUNDOS = 1
CODIGOS_REINTENTABLES = (429, 500, 503, 504)

ERRORES_DE_RED = (
    ConnectionError,
    TimeoutError,
    OSError,
    httpx.ConnectError,
    httpx.TimeoutException,
    httpx.NetworkError,
)


def consultar_asistente_ia(pregunta_usuario: str) -> str:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    configuracion_sistema = types.GenerateContentConfig(
        system_instruction=(
            "Eres el asistente virtual de ExMedAd, un compañero de apoyo para adultos mayores y sus cuidadores. "
            "Responde de forma clara, cálida, sencilla y con un lenguaje muy fácil de entender. "
            "IMPORTANTE: No des diagnósticos definitivos ni recetes medicamentos; siempre recuerda consultar a un médico profesional ante dudas graves."
        ),
        temperature=0.7,
    )

    for intento in range(1, MAX_INTENTOS + 1):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=pregunta_usuario,
                config=configuracion_sistema,
            )

            if not response.text:
                return MENSAJE_ERROR_GENERAL

            return response.text

        except ERRORES_DE_RED as e:
            logger.warning("Intento %d/%d: error de conexión: %s", intento, MAX_INTENTOS, e)
            if intento == MAX_INTENTOS:
                return MENSAJE_SIN_CONEXION
            time.sleep(ESPERA_SEGUNDOS * intento)

        except errors.APIError as e:
            logger.warning("Intento %d/%d: error de la API: %s", intento, MAX_INTENTOS, e)
            if getattr(e, "code", None) in CODIGOS_REINTENTABLES and intento < MAX_INTENTOS:
                time.sleep(ESPERA_SEGUNDOS * intento)
                continue
            return MENSAJE_ERROR_GENERAL

        except Exception as e:
            logger.exception("Error inesperado: %s", e)
            return MENSAJE_ERROR_GENERAL

    return MENSAJE_ERROR_GENERAL
