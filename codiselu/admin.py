from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico,
    GaleriaMultimedia, UsuarioPuntoVisitado, Empresa, OportunidadInversion,
    InversionTurista, Evento, EventoAsistencia, Publicacion, PublicacionImagen,
    ComentarioPublicacion
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'es_protagonista', 'es_turista', 'is_staff')
    list_filter = ('es_protagonista', 'es_turista', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Roles y Perfil', {'fields': ('es_protagonista', 'es_turista', 'telefono', 'foto_perfil')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Roles y Perfil', {'fields': ('es_protagonista', 'es_turista', 'telefono', 'foto_perfil')}),
    )


class DatoHistoricoInline(admin.TabularInline):
    model = DatoHistorico
    extra = 1


class GaleriaMultimediaInline(admin.TabularInline):
    model = GaleriaMultimedia
    extra = 1


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nombre_en', 'nombre_zh', 'latitud_centro', 'longitud_centro', 'ver_circuitos')
    search_fields = ('nombre', 'nombre_en', 'nombre_zh')
    inlines = [DatoHistoricoInline, GaleriaMultimediaInline]
    fieldsets = (
        ('Información General (Español)', {
            'fields': ('nombre', 'descripcion', 'imagen_portada', 'latitud_centro', 'longitud_centro')
        }),
        ('Traducción al Inglés (Auto / Editable)', {
            'fields': ('nombre_en', 'descripcion_en'),
            'classes': ('collapse',)
        }),
        ('Traducción al Mandarín (Auto / Editable)', {
            'fields': ('nombre_zh', 'descripcion_zh'),
            'classes': ('collapse',)
        }),
    )

    def ver_circuitos(self, obj):
        count = obj.circuitos.count()
        return f"{count} circuito(s)"
    ver_circuitos.short_description = "Circuitos"


@admin.register(CircuitoCreativo)
class CircuitoCreativoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'distancia_km', 'duracion_estimada', 'dificultad')
    list_filter = ('ciudad', 'dificultad')
    search_fields = ('nombre', 'nombre_en', 'nombre_zh', 'descripcion')
    fieldsets = (
        ('Información General (Español)', {
            'fields': ('ciudad', 'nombre', 'descripcion', 'distancia_km', 'duracion_estimada', 'dificultad', 'imagen_mapa')
        }),
        ('Traducción al Inglés (Auto / Editable)', {
            'fields': ('nombre_en', 'descripcion_en'),
            'classes': ('collapse',)
        }),
        ('Traducción al Mandarín (Auto / Editable)', {
            'fields': ('nombre_zh', 'descripcion_zh'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PuntoInteres)
class PuntoInteresAdmin(admin.ModelAdmin):
    list_display = ('orden', 'nombre', 'circuito', 'tipo')
    list_filter = ('tipo', 'circuito__ciudad')
    search_fields = ('nombre', 'nombre_en', 'nombre_zh', 'descripcion')
    inlines = [DatoHistoricoInline, GaleriaMultimediaInline]
    fieldsets = (
        ('Información General (Español)', {
            'fields': ('circuito', 'nombre', 'descripcion', 'tipo', 'orden', 'latitud', 'longitud')
        }),
        ('Traducción al Inglés (Auto / Editable)', {
            'fields': ('nombre_en', 'descripcion_en'),
            'classes': ('collapse',)
        }),
        ('Traducción al Mandarín (Auto / Editable)', {
            'fields': ('nombre_zh', 'descripcion_zh'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DatoHistorico)
class DatoHistoricoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'epoca_o_ano', 'ciudad', 'punto_interes')
    list_filter = ('tipo', 'ciudad')
    search_fields = ('titulo', 'titulo_en', 'titulo_zh', 'contenido')
    fieldsets = (
        ('Información General (Español)', {
            'fields': ('ciudad', 'punto_interes', 'titulo', 'tipo', 'contenido', 'epoca_o_ano')
        }),
        ('Traducción al Inglés (Auto / Editable)', {
            'fields': ('titulo_en', 'contenido_en'),
            'classes': ('collapse',)
        }),
        ('Traducción al Mandarín (Auto / Editable)', {
            'fields': ('titulo_zh', 'contenido_zh'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GaleriaMultimedia)
class GaleriaMultimediaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'ciudad', 'punto_interes', 'evento')
    list_filter = ('tipo', 'ciudad', 'evento')


@admin.register(UsuarioPuntoVisitado)
class UsuarioPuntoVisitadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'punto_interes', 'es_validada', 'distancia_metros', 'fecha_visita')
    list_filter = ('es_validada', 'fecha_visita', 'usuario', 'punto_interes__circuito__ciudad')
    search_fields = ('usuario__username', 'punto_interes__nombre')
    readonly_fields = ('es_validada', 'distancia_metros')


class OportunidadInversionInline(admin.TabularInline):
    model = OportunidadInversion
    extra = 1


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'usuario', 'categoria', 'ciudad', 'acepta_inversiones', 'fecha_creacion')
    list_filter = ('acepta_inversiones', 'categoria', 'ciudad')
    search_fields = ('nombre', 'nombre_en', 'nombre_zh', 'descripcion', 'usuario__username')
    inlines = [OportunidadInversionInline]
    fieldsets = (
        ('Información General (Español)', {
            'fields': (
                'usuario', 'ciudad', 'punto_interes', 'nombre', 'descripcion',
                'categoria', 'direccion', 'telefono_contacto', 'email_contacto',
                'sitio_web', 'imagen_portada', 'latitud', 'longitud', 'acepta_inversiones'
            )
        }),
        ('Traducción al Inglés (Auto / Editable)', {
            'fields': ('nombre_en', 'descripcion_en'),
            'classes': ('collapse',)
        }),
        ('Traducción al Mandarín (Auto / Editable)', {
            'fields': ('nombre_zh', 'descripcion_zh'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OportunidadInversion)
class OportunidadInversionAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'empresa', 'monto_requerido', 'monto_recaudado', 'tipo_inversor_permitido', 'esta_activa')
    list_filter = ('esta_activa', 'tipo_inversor_permitido', 'empresa__ciudad')
    search_fields = ('titulo', 'titulo_en', 'titulo_zh', 'descripcion', 'empresa__nombre')
    fieldsets = (
        ('Información General (Español)', {
            'fields': (
                'empresa', 'titulo', 'descripcion', 'monto_requerido',
                'monto_minimo_inversion', 'monto_recaudado', 'retorno_estimado',
                'tipo_inversor_permitido', 'esta_activa'
            )
        }),
        ('Traducción al Inglés (Auto / Editable)', {
            'fields': ('titulo_en', 'descripcion_en'),
            'classes': ('collapse',)
        }),
        ('Traducción al Mandarín (Auto / Editable)', {
            'fields': ('titulo_zh', 'descripcion_zh'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InversionTurista)
class InversionTuristaAdmin(admin.ModelAdmin):
    list_display = ('id', 'inversionista', 'oportunidad', 'monto_propuesto', 'tipo_inversor', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'tipo_inversor', 'fecha_solicitud')
    search_fields = ('inversionista__username', 'oportunidad__titulo', 'oportunidad__empresa__nombre')


class EventoAsistenciaInline(admin.TabularInline):
    model = EventoAsistencia
    extra = 0


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'creador', 'empresa', 'ciudad', 'fecha_inicio', 'total_granos_cafe', 'total_asistentes', 'es_oficial', 'esta_activo')
    list_filter = ('es_oficial', 'esta_activo', 'es_gratuito', 'ciudad', 'fecha_inicio')
    search_fields = ('titulo', 'titulo_en', 'titulo_zh', 'descripcion', 'ubicacion', 'creador__username', 'empresa__nombre')
    inlines = [GaleriaMultimediaInline, EventoAsistenciaInline]
    fieldsets = (
        ('Información General (Español)', {
            'fields': (
                'creador', 'empresa', 'ciudad', 'titulo', 'descripcion',
                'fecha_inicio', 'fecha_fin', 'ubicacion', 'latitud', 'longitud',
                'imagen', 'precio_entrada', 'es_gratuito', 'cupo_maximo',
                'es_oficial', 'dias_previos_mural', 'esta_activo'
            )
        }),
        ('Traducción al Inglés (Auto / Editable)', {
            'fields': ('titulo_en', 'descripcion_en'),
            'classes': ('collapse',)
        }),
        ('Traducción al Mandarín (Auto / Editable)', {
            'fields': ('titulo_zh', 'descripcion_zh'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EventoAsistencia)
class EventoAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'evento', 'fecha_registro')
    list_filter = ('fecha_registro', 'evento')
    search_fields = ('usuario__username', 'evento__titulo')


class PublicacionImagenInline(admin.TabularInline):
    model = PublicacionImagen
    extra = 1


class ComentarioPublicacionInline(admin.TabularInline):
    model = ComentarioPublicacion
    extra = 1


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'autor', 'titulo', 'empresa', 'ciudad', 'evento', 'total_likes', 'total_comentarios', 'esta_activa', 'fecha_creacion')
    list_filter = ('esta_activa', 'ciudad', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion', 'autor__username', 'empresa__nombre')
    inlines = [PublicacionImagenInline, ComentarioPublicacionInline]


@admin.register(ComentarioPublicacion)
class ComentarioPublicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'autor', 'publicacion', 'contenido', 'esta_activo', 'fecha_creacion')
    list_filter = ('esta_activo', 'fecha_creacion')
    search_fields = ('contenido', 'autor__username', 'publicacion__titulo')





