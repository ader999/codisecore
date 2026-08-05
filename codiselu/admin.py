from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico, GaleriaMultimedia
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
    list_display = ('titulo', 'tipo', 'ciudad', 'punto_interes')
    list_filter = ('tipo', 'ciudad')

