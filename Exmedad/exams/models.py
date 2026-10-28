from django.db import models

class ExamenHistorial(models.Model):
    titulo = models.CharField(max_length=100, default="Examen Médico")
    resumen_general = models.TextField(help_text="Resumen general en palabras sencillas")
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.fecha.strftime('%d/%m/%Y')}"


class ParametroExamen(models.Model):
    examen = models.ForeignKey(ExamenHistorial, related_name='parametros', on_delete=models.CASCADE)
    
    nombre_parametro = models.CharField(max_length=100) 
    valor_obtenido = models.CharField(max_length=50)    
    estado_semaforo = models.CharField(max_length=20)   
    explicacion_coloquial = models.TextField()          

    def __str__(self):
        return f"{self.nombre_parametro} ({self.estado_semaforo}) - {self.examen.titulo}"
