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
    nombre_en = models.CharField(max_length=100, blank=True, null=True, help_text="Traducción al inglés")
    nombre_zh = models.CharField(max_length=100, blank=True, null=True, help_text="Traducción al mandarín")
    descripcion = models.TextField()
    descripcion_en = models.TextField(blank=True, null=True, help_text="Traducción al inglés")
    descripcion_zh = models.TextField(blank=True, null=True, help_text="Traducción al mandarín")
    imagen_portada = models.ImageField(upload_to='ciudades/portadas/', blank=True, null=True)
    latitud_centro = models.FloatField()
    longitud_centro = models.FloatField()

    class Meta:
        verbose_name_plural = "Ciudades"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        from .translation_service import auto_completar_traducciones
        auto_completar_traducciones(self, ['nombre', 'descripcion'])
        super().save(*args, **kwargs)


class CircuitoCreativo(models.Model):
    DIFICULTAD_CHOICES = [
        ('Baja', 'Baja'),
        ('Media', 'Media'),
        ('Alta', 'Alta'),
    ]

    ciudad = models.ForeignKey(Ciudad, related_name='circuitos', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150)
    nombre_en = models.CharField(max_length=150, blank=True, null=True, help_text="Traducción al inglés")
    nombre_zh = models.CharField(max_length=150, blank=True, null=True, help_text="Traducción al mandarín")
    descripcion = models.TextField()
    descripcion_en = models.TextField(blank=True, null=True, help_text="Traducción al inglés")
    descripcion_zh = models.TextField(blank=True, null=True, help_text="Traducción al mandarín")
    distancia_km = models.DecimalField(max_digits=5, decimal_places=2)
    duracion_estimada = models.CharField(max_length=50)
    dificultad = models.CharField(max_length=10, choices=DIFICULTAD_CHOICES, default='Baja')
    imagen_mapa = models.ImageField(upload_to='circuitos/mapas/', blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.ciudad.nombre})"

    def save(self, *args, **kwargs):
        from .translation_service import auto_completar_traducciones
        auto_completar_traducciones(self, ['nombre', 'descripcion'])
        super().save(*args, **kwargs)


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
    nombre_en = models.CharField(max_length=150, blank=True, null=True, help_text="Traducción al inglés")
    nombre_zh = models.CharField(max_length=150, blank=True, null=True, help_text="Traducción al mandarín")
    descripcion = models.TextField()
    descripcion_en = models.TextField(blank=True, null=True, help_text="Traducción al inglés")
    descripcion_zh = models.TextField(blank=True, null=True, help_text="Traducción al mandarín")
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

    def save(self, *args, **kwargs):
        from .translation_service import auto_completar_traducciones
        auto_completar_traducciones(self, ['nombre', 'descripcion'])
        super().save(*args, **kwargs)


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
    titulo_en = models.CharField(max_length=200, blank=True, null=True, help_text="Traducción al inglés")
    titulo_zh = models.CharField(max_length=200, blank=True, null=True, help_text="Traducción al mandarín")
    tipo = models.CharField(max_length=20, choices=TIPO_DATOS_CHOICES, default='Hito')
    contenido = models.TextField()
    contenido_en = models.TextField(blank=True, null=True, help_text="Traducción al inglés")
    contenido_zh = models.TextField(blank=True, null=True, help_text="Traducción al mandarín")
    epoca_o_ano = models.CharField(max_length=50, blank=True, null=True, help_text="Ej: Siglo XVI, 1912, Época Colonial")

    class Meta:
        verbose_name = "Dato Histórico"
        verbose_name_plural = "Datos Históricos"

    def __str__(self):
        origen = self.ciudad.nombre if self.ciudad else (self.punto_interes.nombre if self.punto_interes else "General")
        return f"{self.titulo} - [{origen}] ({self.tipo})"

    def save(self, *args, **kwargs):
        from .translation_service import auto_completar_traducciones
        auto_completar_traducciones(self, ['titulo', 'contenido'])
        super().save(*args, **kwargs)


from django.utils import timezone

class GaleriaMultimedia(models.Model):
    TIPO_CHOICES = [
        ('Imagen', 'Imagen'),
        ('Video', 'Video'),
    ]

    ciudad = models.ForeignKey(Ciudad, related_name='galeria', on_delete=models.CASCADE, null=True, blank=True)
    punto_interes = models.ForeignKey(PuntoInteres, related_name='galeria', on_delete=models.CASCADE, null=True, blank=True)
    evento = models.ForeignKey('Evento', related_name='galeria', on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=150, blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='Imagen')
    imagen = models.ImageField(upload_to='galeria/imagenes/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text="URL de YouTube, Vimeo o servidor de video")

    class Meta:
        verbose_name = "Galería Multimedia"
        verbose_name_plural = "Galerías Multimedia"

    def __str__(self):
        origen = self.ciudad.nombre if self.ciudad else (self.punto_interes.nombre if self.punto_interes else (self.evento.titulo if self.evento else "General"))
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
    nombre_en = models.CharField(max_length=200, blank=True, null=True, help_text="Traducción al inglés")
    nombre_zh = models.CharField(max_length=200, blank=True, null=True, help_text="Traducción al mandarín")
    descripcion = models.TextField()
    descripcion_en = models.TextField(blank=True, null=True, help_text="Traducción al inglés")
    descripcion_zh = models.TextField(blank=True, null=True, help_text="Traducción al mandarín")
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

    def save(self, *args, **kwargs):
        from .translation_service import auto_completar_traducciones
        auto_completar_traducciones(self, ['nombre', 'descripcion'])
        super().save(*args, **kwargs)


class OportunidadInversion(models.Model):
    TIPO_INVERSOR_CHOICES = [
        ('Todos', 'Nacionales y Extranjeros'),
        ('Nacional', 'Solo Nacionales'),
        ('Extranjero', 'Solo Extranjeros'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='oportunidades_inversion')
    titulo = models.CharField(max_length=200)
    titulo_en = models.CharField(max_length=200, blank=True, null=True, help_text="Traducción al inglés")
    titulo_zh = models.CharField(max_length=200, blank=True, null=True, help_text="Traducción al mandarín")
    descripcion = models.TextField()
    descripcion_en = models.TextField(blank=True, null=True, help_text="Traducción al inglés")
    descripcion_zh = models.TextField(blank=True, null=True, help_text="Traducción al mandarín")
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

    def save(self, *args, **kwargs):
        from .translation_service import auto_completar_traducciones
        auto_completar_traducciones(self, ['titulo', 'descripcion'])
        super().save(*args, **kwargs)


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
    titulo_en = models.CharField(max_length=200, blank=True, null=True, help_text="Traducción al inglés")
    titulo_zh = models.CharField(max_length=200, blank=True, null=True, help_text="Traducción al mandarín")
    descripcion = models.TextField()
    descripcion_en = models.TextField(blank=True, null=True, help_text="Traducción al inglés")
    descripcion_zh = models.TextField(blank=True, null=True, help_text="Traducción al mandarín")
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
    granos_cafe = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='eventos_grano_cafe', blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

    def save(self, *args, **kwargs):
        from .translation_service import auto_completar_traducciones
        auto_completar_traducciones(self, ['titulo', 'descripcion'])
        super().save(*args, **kwargs)

    @property
    def en_mural(self):
        from django.utils import timezone
        ahora = timezone.now()
        fecha_visibilidad = self.fecha_inicio - timezone.timedelta(days=self.dias_previos_mural)
        if self.fecha_fin:
            return fecha_visibilidad <= ahora <= self.fecha_fin
        return fecha_visibilidad <= ahora <= (self.fecha_inicio + timezone.timedelta(days=1))

    @property
    def total_granos_cafe(self):
        return self.granos_cafe.count()

    @property
    def total_asistentes(self):
        return self.asistencias.count()

    def __str__(self):
        tipo = "Oficial" if self.es_oficial else "Protagonista"
        return f"[{tipo}] {self.titulo} - {self.fecha_inicio.strftime('%Y-%m-%d %H:%M')}"


class EventoAsistencia(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='asistencias_eventos')
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='asistencias')
    fecha_registro = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('usuario', 'evento')
        verbose_name = "Asistencia a Evento"
        verbose_name_plural = "Asistencias a Eventos"

    def __str__(self):
        return f"{self.usuario.username} asistirá a {self.evento.titulo}"


class Publicacion(models.Model):
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='publicaciones')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name='publicaciones')
    ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE, null=True, blank=True, related_name='publicaciones')
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, null=True, blank=True, related_name='publicaciones')
    titulo = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField()
    imagen_principal = models.ImageField(upload_to='publicaciones/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='publicaciones_dado_like', blank=True)
    esta_activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"

    @property
    def total_likes(self):
        return self.likes.count()

    @property
    def total_comentarios(self):
        return self.comentarios.filter(esta_activo=True).count()

    def __str__(self):
        return f"Publicación de {self.autor.username} - {self.fecha_creacion.strftime('%Y-%m-%d')}"


class PublicacionImagen(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='publicaciones/colecciones/')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Imagen de Publicación"
        verbose_name_plural = "Imágenes de Publicaciones"

    def __str__(self):
        return f"Imagen #{self.id} de Publicación {self.publicacion_id}"


class ComentarioPublicacion(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comentarios_publicaciones')
    contenido = models.TextField()
    esta_activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_creacion']
        verbose_name = "Comentario de Publicación"
        verbose_name_plural = "Comentarios de Publicaciones"

    def __str__(self):
        return f"Comentario de {self.autor.username} en Publicación #{self.publicacion_id}"


