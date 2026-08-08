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


class Empresa(models.Model):
    TIPO_EMPRESA_CHOICES = [
        ('Gastronomia', 'Gastronomía / Restaurante'),
        ('Hospedaje', 'Hotel / Hospedaje'),
        ('Taller', 'Taller Artesanal / Galería'),
        ('Destino', 'Destino Turístico / Sitio de Interés'),
        ('Servicios', 'Servicios Turísticos / Tours'),
        ('Otro', 'Otro'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='empresas')
    ciudad = models.ForeignKey(Ciudad, on_delete=models.SET_NULL, null=True, blank=True, related_name='empresas')
    punto_interes = models.ForeignKey(PuntoInteres, on_delete=models.SET_NULL, null=True, blank=True, related_name='empresas')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=50, choices=TIPO_EMPRESA_CHOICES, default='Destino')
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono_contacto = models.CharField(max_length=20, blank=True, null=True)
    email_contacto = models.EmailField(blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)
    imagen_portada = models.ImageField(upload_to='empresas/portadas/', blank=True, null=True)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    acepta_inversiones = models.BooleanField(default=False, help_text="Indica si esta empresa o destino turístico acepta ofertas o proyectos de inversión")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Empresa / Destino Turístico"
        verbose_name_plural = "Empresas y Destinos Turísticos"

    def __str__(self):
        return f"{self.nombre} ({self.usuario.username})"


class OportunidadInversion(models.Model):
    TIPO_INVERSOR_CHOICES = [
        ('Todos', 'Nacionales y Extranjeros'),
        ('Nacional', 'Solo Nacionales'),
        ('Extranjero', 'Solo Extranjeros'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='oportunidades_inversion')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    monto_requerido = models.DecimalField(max_digits=12, decimal_places=2, help_text="Monto objetivo de inversión en USD o C$")
    monto_minimo_inversion = models.DecimalField(max_digits=12, decimal_places=2, default=100.00, help_text="Monto mínimo para invertir")
    monto_recaudado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    retorno_estimado = models.CharField(max_length=150, blank=True, null=True, help_text="Ejemplo: 15% rendimiento anual, participación de utilidades")
    tipo_inversor_permitido = models.CharField(max_length=20, choices=TIPO_INVERSOR_CHOICES, default='Todos')
    esta_activa = models.BooleanField(default=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Oportunidad de Inversión"
        verbose_name_plural = "Oportunidades de Inversión"

    def __str__(self):
        return f"Oportunidad: {self.titulo} - {self.empresa.nombre}"


class InversionTurista(models.Model):
    TIPO_INVERSOR_CHOICES = [
        ('Nacional', 'Turista / Inversionista Nacional'),
        ('Extranjero', 'Turista / Inversionista Extranjero'),
    ]
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente de revisión'),
        ('Aprobada', 'Aprobada / Confirmada'),
        ('Rechazada', 'Rechazada'),
    ]

    inversionista = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inversiones_realizadas')
    oportunidad = models.ForeignKey(OportunidadInversion, on_delete=models.CASCADE, related_name='solicitudes_inversion')
    monto_propuesto = models.DecimalField(max_digits=12, decimal_places=2)
    tipo_inversor = models.CharField(max_length=20, choices=TIPO_INVERSOR_CHOICES, default='Nacional')
    mensaje = models.TextField(blank=True, null=True, help_text="Mensaje o propuesta enviada por el turista/inversionista")
    telefono_inversor = models.CharField(max_length=20, blank=True, null=True)
    email_inversor = models.EmailField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inversión de Turista"
        verbose_name_plural = "Inversiones de Turistas"

    def __str__(self):
        return f"Inversión de {self.inversionista.username} en {self.oportunidad.empresa.nombre} (${self.monto_propuesto})"


class Evento(models.Model):
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='eventos_creados')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='eventos', null=True, blank=True)
    ciudad = models.ForeignKey(Ciudad, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    ubicacion = models.CharField(max_length=255, help_text="Dirección o punto del evento")
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)
    imagen = models.ImageField(upload_to='eventos/', blank=True, null=True)
    precio_entrada = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    es_gratuito = models.BooleanField(default=True)
    cupo_maximo = models.PositiveIntegerField(null=True, blank=True)
    es_oficial = models.BooleanField(default=False, help_text="Indica si es un evento oficial de la ciudad publicado por administradores")
    dias_previos_mural = models.PositiveIntegerField(default=7, help_text="Días antes de la fecha de inicio en los que el evento aparece en el mural de publicación")
    esta_activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

    @property
    def en_mural(self):
        from django.utils import timezone
        ahora = timezone.now()
        fecha_visibilidad = self.fecha_inicio - timezone.timedelta(days=self.dias_previos_mural)
        if self.fecha_fin:
            return fecha_visibilidad <= ahora <= self.fecha_fin
        return fecha_visibilidad <= ahora <= (self.fecha_inicio + timezone.timedelta(days=1))

    def __str__(self):
        tipo = "Oficial" if self.es_oficial else "Protagonista"
        return f"[{tipo}] {self.titulo} - {self.fecha_inicio.strftime('%Y-%m-%d %H:%M')}"

