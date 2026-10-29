# ExMedAd — Cuidado Adulto Mayor

ExMedAd es una aplicación web desarrollada en Django diseñada para asistir a adultos mayores y a sus familias en la comprensión de sus exámenes e informes médicos. A través de inteligencia artificial, la plataforma convierte reportes técnicos complejos en paneles visuales sencillos con resúmenes claros, explicaciones en lenguaje coloquial e indicadores de semáforo (verde, amarillo y rojo).

# Requisitos Previos
* **Python** (versión 3.10 o superior)
* **Git**
* Un entorno virtual de Python (`venv`)
* Clave de API de **Groq** (*Groq API Key*)

# Instrucciones de Instalación y Ejecución Local
Sigue estos pasos en tu terminal para clonar y ejecutar el proyecto en tu computadora:

1. Clonar el repositorio

```bash
git clone https://github.com/Mirzzo0o/ExMedAd
```
2. Crear y activar el entorno virtual

En Windows (PowerShell):

```bash
python -m venv venv
.\venv\Scripts\activate
```

En Windows (Cmd):

```bash
python -m venv venv
venv\Scripts\activate.bat
```

En macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Instalar dependencias

Asegúrate de tener el entorno virtual activo e instala las dependencias requeridas (incluyendo Django, pypdf y el cliente de OpenAI para Groq):

```bash
pip install -r requirements.txt
```

4. Configurar la clave de API de Groq

La aplicación utiliza el modelo openai/gpt-oss-20b a través de la API de Groq. Configura la variable de entorno según tu sistema operativo antes de iniciar la aplicación:

En Windows (PowerShell):

```bash
$env:GROQ_API_KEY="tu_clave_aqui"
```

En Windows (CMD):

```bash
set GROQ_API_KEY=tu_clave_aqui
```

En macOS / Linux:

```bash
export GROQ_API_KEY="tu_clave_aqui"
```

5. Aplicar migraciones de la base de datos

```bash
python manage.py makemigrations
python manage.py migrate
```

6. Iniciar el servidor de desarrollo de Django

```bash
python manage.py runserver
```

Abre tu navegador e ingresa a: http://127.0.0.1:8000/