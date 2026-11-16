import os
import time
import logging
import groq
from groq import Groq

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

MODELO = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_INTENTOS = 3
ESPERA_SEGUNDOS = 1
TIMEOUT_SEGUNDOS = 20

ERRORES_DE_RED = (
    ConnectionError,
    TimeoutError,
    OSError,
    groq.APIConnectionError,
    groq.APITimeoutError,
)

SYSTEM_INSTRUCTION = (
    "Eres el asistente virtual de ExMedAd, un compañero de apoyo para adultos mayores y sus cuidadores. "
    "Responde de forma clara, cálida, sencilla y con un lenguaje muy fácil de entender. "
    "Escribe solo texto plano: no uses asteriscos, tablas, encabezados ni formato Markdown. "
    "IMPORTANTE: No des diagnósticos definitivos ni recetes medicamentos; siempre recuerda consultar a un médico profesional ante dudas graves."
)


def _es_reintentable(error):
    if isinstance(error, groq.RateLimitError):
        return True
    return error.status_code >= 500


def consultar_asistente_ia(pregunta_usuario: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("Falta la variable de entorno GROQ_API_KEY")
        return MENSAJE_ERROR_GENERAL

    client = Groq(api_key=api_key, timeout=TIMEOUT_SEGUNDOS, max_retries=0)

    for intento in range(1, MAX_INTENTOS + 1):
        try:
            response = client.chat.completions.create(
                model=MODELO,
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": pregunta_usuario},
                ],
                temperature=0.7,
            )

            texto = ""
            if response and response.choices:
                texto = (response.choices[0].message.content or "").strip()

            if not texto:
                logger.warning("Intento %d/%d: respuesta vacía de Groq", intento, MAX_INTENTOS)
                return MENSAJE_ERROR_GENERAL

            return texto

        except ERRORES_DE_RED as e:
            logger.warning("Intento %d/%d: error de conexión: %s", intento, MAX_INTENTOS, e)
            if intento == MAX_INTENTOS:
                return MENSAJE_SIN_CONEXION
            time.sleep(ESPERA_SEGUNDOS * intento)

        except groq.APIStatusError as e:
            logger.warning("Intento %d/%d: error de la API de Groq (%s): %s", intento, MAX_INTENTOS, e.status_code, e)
            if _es_reintentable(e) and intento < MAX_INTENTOS:
                time.sleep(ESPERA_SEGUNDOS * intento)
                continue
            return MENSAJE_ERROR_GENERAL

        except Exception as e:
            logger.exception("Error inesperado: %s", e)
            return MENSAJE_ERROR_GENERAL

    return MENSAJE_ERROR_GENERAL