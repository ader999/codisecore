from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    es_protagonista = models.BooleanField(default=False)
    es_turista = models.BooleanField(default=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)

    def __str__(self):
        return self.username


class Ciudad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    imagen_portada = models.ImageField(upload_to='ciudades/portadas/', blank=True, null=True)
    latitud_centro = models.FloatField()
    longitud_centro = models.FloatField()

    class Meta:
        verbose_name_plural = "Ciudades"

    def __str__(self):
        return self.nombre


class CircuitoCreativo(models.Model):
    DIFICULTAD_CHOICES = [
        ('Baja', 'Baja'),
        ('Media', 'Media'),
        ('Alta', 'Alta'),
    ]

    ciudad = models.ForeignKey(Ciudad, related_name='circuitos', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    distancia_km = models.DecimalField(max_digits=5, decimal_places=2)
    duracion_estimada = models.CharField(max_length=50)
    dificultad = models.CharField(max_length=10, choices=DIFICULTAD_CHOICES, default='Baja')
    imagen_mapa = models.ImageField(upload_to='circuitos/mapas/', blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.ciudad.nombre})"


class PuntoInteres(models.Model):
    TIPO_PUNTO_CHOICES = [
        ('Historico', 'Sitio Histórico'),
        ('Cultural', 'Sitio Cultural / Galería / Museo'),
        ('Natural', 'Sitio Natural'),
        ('Taller', 'Taller Artesanal / Saber Popular'),
        ('Gastronomico', 'Gastronomía Tradicional'),
    ]

    circuito = models.ForeignKey(CircuitoCreativo, related_name='puntos_interes', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_PUNTO_CHOICES, default='Cultural')
    orden = models.PositiveIntegerField(default=1, help_text="Orden dentro del circuito")
    latitud = models.FloatField()
    longitud = models.FloatField()

    class Meta:
        ordering = ['orden']
        verbose_name = "Punto de Interés"
        verbose_name_plural = "Puntos de Interés"

    def __str__(self):
        return f"{self.orden}. {self.nombre} ({self.circuito.nombre})"


class DatoHistorico(models.Model):
    TIPO_DATOS_CHOICES = [
        ('Hito', 'Hito Histórico'),
        ('Leyenda', 'Mito o Leyenda'),
        ('SaberPopular', 'Saber Popular / Tradición'),
        ('Gastronomia', 'Dato Gastronómico'),
    ]

    ciudad = models.ForeignKey(Ciudad, related_name='datos_historicos', on_delete=models.CASCADE, null=True, blank=True)
    punto_interes = models.ForeignKey(PuntoInteres, related_name='datos_historicos', on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_DATOS_CHOICES, default='Hito')
    contenido = models.TextField()
    epoca_o_ano = models.CharField(max_length=50, blank=True, null=True, help_text="Ej: Siglo XVI, 1912, Época Colonial")

    class Meta:
        verbose_name = "Dato Histórico"
        verbose_name_plural = "Datos Históricos"

    def __str__(self):
        origen = self.ciudad.nombre if self.ciudad else (self.punto_interes.nombre if self.punto_interes else "General")
        return f"{self.titulo} - [{origen}] ({self.tipo})"


from django.utils import timezone

class GaleriaMultimedia(models.Model):
    TIPO_CHOICES = [
        ('Imagen', 'Imagen'),
        ('Video', 'Video'),
    ]

    ciudad = models.ForeignKey(Ciudad, related_name='galeria', on_delete=models.CASCADE, null=True, blank=True)
    punto_interes = models.ForeignKey(PuntoInteres, related_name='galeria', on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=150, blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='Imagen')
    imagen = models.ImageField(upload_to='galeria/imagenes/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text="URL de YouTube, Vimeo o servidor de video")

    class Meta:
        verbose_name = "Galería Multimedia"
        verbose_name_plural = "Galerías Multimedia"

    def __str__(self):
        origen = self.ciudad.nombre if self.ciudad else (self.punto_interes.nombre if self.punto_interes else "General")
        return f"{self.tipo}: {self.titulo or 'Sin título'} [{origen}]"


class UsuarioPuntoVisitado(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='puntos_visitados')
    punto_interes = models.ForeignKey(PuntoInteres, on_delete=models.CASCADE, related_name='visitas_usuarios')
    fecha_visita = models.DateTimeField(default=timezone.now)
    latitud_usuario = models.FloatField(null=True, blank=True, help_text="Latitud GPS reportada por el usuario")
    longitud_usuario = models.FloatField(null=True, blank=True, help_text="Longitud GPS reportada por el usuario")
    es_validada = models.BooleanField(default=False, help_text="Indica si la visita fue validada por estar en/cerca del punto")
    distancia_metros = models.FloatField(null=True, blank=True, help_text="Distancia calculada en metros entre el usuario y el punto de interés")

    class Meta:
        db_table = 'usuario_puntos_visitados'
        unique_together = ('usuario', 'punto_interes')
        ordering = ['-fecha_visita']
        verbose_name = "Punto Visitado"
        verbose_name_plural = "Puntos Visitados"

    def __str__(self):
        estado = "Validada" if self.es_validada else "No validada"
        return f"{self.usuario.username} visitó {self.punto_interes.nombre} ({estado})"



