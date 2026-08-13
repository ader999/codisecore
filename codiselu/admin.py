from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico,
    GaleriaMultimedia, UsuarioPuntoVisitado, Empresa, OportunidadInversion,
    InversionTurista, Evento, EventoAsistencia, Publicacion, PublicacionImagen
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
    list_display = ('nombre', 'latitud_centro', 'longitud_centro', 'ver_circuitos')
    search_fields = ('nombre',)
    inlines = [DatoHistoricoInline, GaleriaMultimediaInline]

    def ver_circuitos(self, obj):
        count = obj.circuitos.count()
        return f"{count} circuito(s)"
    ver_circuitos.short_description = "Circuitos"


@admin.register(CircuitoCreativo)
class CircuitoCreativoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'distancia_km', 'duracion_estimada', 'dificultad')
    list_filter = ('ciudad', 'dificultad')


@admin.register(PuntoInteres)
class PuntoInteresAdmin(admin.ModelAdmin):
    list_display = ('orden', 'nombre', 'circuito', 'tipo')
    list_filter = ('tipo', 'circuito__ciudad')
    inlines = [DatoHistoricoInline, GaleriaMultimediaInline]


@admin.register(DatoHistorico)
class DatoHistoricoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'epoca_o_ano', 'ciudad', 'punto_interes')
    list_filter = ('tipo', 'ciudad')


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
    search_fields = ('nombre', 'descripcion', 'usuario__username')
    inlines = [OportunidadInversionInline]


@admin.register(OportunidadInversion)
class OportunidadInversionAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'empresa', 'monto_requerido', 'monto_recaudado', 'tipo_inversor_permitido', 'esta_activa')
    list_filter = ('esta_activa', 'tipo_inversor_permitido', 'empresa__ciudad')
    search_fields = ('titulo', 'descripcion', 'empresa__nombre')


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
    search_fields = ('titulo', 'descripcion', 'ubicacion', 'creador__username', 'empresa__nombre')
    inlines = [GaleriaMultimediaInline, EventoAsistenciaInline]


@admin.register(EventoAsistencia)
class EventoAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'evento', 'fecha_registro')
    list_filter = ('fecha_registro', 'evento')
    search_fields = ('usuario__username', 'evento__titulo')


class PublicacionImagenInline(admin.TabularInline):
    model = PublicacionImagen
    extra = 1


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'autor', 'titulo', 'empresa', 'ciudad', 'evento', 'total_likes', 'esta_activa', 'fecha_creacion')
    list_filter = ('esta_activa', 'ciudad', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion', 'autor__username', 'empresa__nombre')
    inlines = [PublicacionImagenInline]




