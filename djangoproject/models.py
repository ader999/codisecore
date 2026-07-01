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
    imagen_portada = models.ImageField(upload_to='ciudades/portadas/')
    latitud_centro = models.FloatField()
    longitud_centro = models.FloatField()

    class Meta:
        verbose_name_plural = "Ciudades"

    def __str__(self):
        return self.nombre