from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Ciudad, CircuitoCreativo
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


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'latitud_centro', 'longitud_centro', 'ver_circuitos')
    search_fields = ('nombre',)

    def ver_circuitos(self, obj):
        count = obj.circuitos.count()
        return f"{count} circuito(s)"
    ver_circuitos.short_description = "Circuitos"
