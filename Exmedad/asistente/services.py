import os
from google import genai
from google.genai import types

def consultar_asistente_ia(pregunta_usuario: str):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    configuracion_sistema = types.GenerateContentConfig(
        system_instruction=(
            "Eres el asistente virtual de ExMedAd, un compañero de apoyo para adultos mayores y sus cuidadores. "
            "Responde de forma clara, cálida, sencilla y con un lenguaje muy fácil de entender. "
            "IMPORTANTE: No des diagnósticos definitivos ni recetes medicamentos; siempre recuerda consultar a un médico profesional ante dudas graves."
        ),
        temperature=0.7,
    )

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=pregunta_usuario,
        config=configuracion_sistema,
    )
    
    return response.text
