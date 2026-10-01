from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import FileResponse
from .models import (
    User, Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico,
    GaleriaMultimedia, UsuarioPuntoVisitado, Empresa, EmpresaMiembro, OportunidadInversion,
    InversionTurista, Evento, EventoAsistencia, Publicacion, PublicacionImagen,
    ComentarioPublicacion
)
from .pdf_export_service import generar_pdf_traduccion_miskito
from .excel_export_service import generar_excel_traduccion_miskito

# Personalización del Panel de Control Codice路
admin.site.site_header = "Codice路"
admin.site.site_title = "Codice路"
admin.site.index_title = "Panel de Control Codice路"

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


class OcultarTraduccionesAlCrearMixin:
    """
    Mixin para ModelAdmin que oculta las secciones de traducción (Inglés, Mandarín, Miskito)
    durante la creación inicial de un registro (obj is None) para evitar confusión al usuario.
    El sistema autocompleta las traducciones al guardar mediante save().
    Una vez guardado el registro (obj is not None), se muestran las secciones de traducción
    para que puedan ser revisadas o editadas manualmente.
    """
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is None:
            return [
                fs for fs in fieldsets
                if not any(kw in fs[0].lower() for kw in ['inglés', 'ingles', 'mandarín', 'mandarin', 'miskito', 'miskitu', 'traducción', 'traduccion'])
            ]
        return fieldsets


class DatoHistoricoInline(admin.TabularInline):
    model = DatoHistorico
    extra = 1

    def get_fields(self, request, obj=None):
        if obj is None:
            return ('titulo', 'tipo', 'contenido', 'epoca_o_ano')
        return ('titulo', 'tipo', 'contenido', 'epoca_o_ano', 'titulo_en', 'titulo_zh', 'titulo_miq', 'contenido_en', 'contenido_zh', 'contenido_miq')


class GaleriaMultimediaInline(admin.TabularInline):
    model = GaleriaMultimedia
    extra = 1
    fields = ('titulo', 'tipo', 'imagen', 'video_archivo', 'video_url')


@admin.register(Ciudad)
class CiudadAdmin(OcultarTraduccionesAlCrearMixin, admin.ModelAdmin):
    list_display = ('nombre', 'nombre_en', 'nombre_zh', 'nombre_miq', 'latitud_centro', 'longitud_centro', 'ver_circuitos')
    search_fields = ('nombre', 'nombre_en', 'nombre_zh', 'nombre_miq')
    inlines = [DatoHistoricoInline, GaleriaMultimediaInline]
    actions = ['exportar_a_pdf_miskito']
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
        ('Traducción al Miskito (Manual)', {
            'fields': ('nombre_miq', 'descripcion_miq'),
            'classes': ('collapse',)
        }),
    )

    def ver_circuitos(self, obj):
        count = obj.circuitos.count()
        return f"{count} circuito(s)"
    ver_circuitos.short_description = "Circuitos"

    actions = ['exportar_a_pdf_miskito_horizontal', 'exportar_a_excel_miskito', 'exportar_a_pdf_miskito_completo', 'exportar_a_pdf_miskito']

    @admin.action(description="📐 Exportar a PDF Miskito Horizontal (Hoja apaisada con columna ampliada)")
    def exportar_a_pdf_miskito_horizontal(self, request, queryset):
        ciudades_con_circuitos = queryset.filter(circuitos__isnull=False).distinct()
        if not ciudades_con_circuitos.exists():
            self.message_user(
                request,
                "Ninguna de las ciudades seleccionadas tiene circuitos creativos para traducir.",
                level=messages.WARNING
            )
            return None

        ciudades_ids = list(ciudades_con_circuitos.values_list('id', flat=True))
        pdf_buffer = generar_pdf_traduccion_miskito(ciudades_ids=ciudades_ids, solo_pendientes=True, orientacion='horizontal')
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Codice_Traduccion_Miskito_Horizontal.pdf"'
        return response

    @admin.action(description="📊 Exportar a Excel Miskito (Solo lo pendiente por traducir)")
    def exportar_a_excel_miskito(self, request, queryset):
        ciudades_con_circuitos = queryset.filter(circuitos__isnull=False).distinct()
        if not ciudades_con_circuitos.exists():
            self.message_user(
                request,
                "Ninguna de las ciudades seleccionadas tiene circuitos creativos para traducir.",
                level=messages.WARNING
            )
            return None

        ciudades_ids = list(ciudades_con_circuitos.values_list('id', flat=True))
        excel_buffer = generar_excel_traduccion_miskito(ciudades_ids=ciudades_ids, solo_pendientes=True)
        response = FileResponse(
            excel_buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="Codice_Plantilla_Miskito_Pendientes.xlsx"'
        return response

    @admin.action(description="📄 Exportar a PDF Miskito (Solo lo pendiente por traducir)")
    def exportar_a_pdf_miskito(self, request, queryset):
        ciudades_con_circuitos = queryset.filter(circuitos__isnull=False).distinct()
        if not ciudades_con_circuitos.exists():
            self.message_user(
                request,
                "Ninguna de las ciudades seleccionadas tiene circuitos creativos para traducir.",
                level=messages.WARNING
            )
            return None

        ciudades_ids = list(ciudades_con_circuitos.values_list('id', flat=True))
        pdf_buffer = generar_pdf_traduccion_miskito(ciudades_ids=ciudades_ids, solo_pendientes=True, orientacion='vertical')
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Codice_Traduccion_Miskito_Pendientes.pdf"'
        return response

    @admin.action(description="📚 Exportar a PDF Miskito (Completo con todos los elementos)")
    def exportar_a_pdf_miskito_completo(self, request, queryset):
        ciudades_con_circuitos = queryset.filter(circuitos__isnull=False).distinct()
        if not ciudades_con_circuitos.exists():
            self.message_user(
                request,
                "Ninguna de las ciudades seleccionadas tiene circuitos creativos.",
                level=messages.WARNING
            )
            return None

        ciudades_ids = list(ciudades_con_circuitos.values_list('id', flat=True))
        pdf_buffer = generar_pdf_traduccion_miskito(ciudades_ids=ciudades_ids, solo_pendientes=False, orientacion='vertical')
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Codice_Traduccion_Miskito_Completo.pdf"'
        return response

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                'exportar-miskito-pdf/',
                self.admin_site.admin_view(self.vista_exportar_miskito_pdf),
                name='codiselu_ciudad_exportar_miskito'
            ),
            path(
                'exportar-miskito-excel/',
                self.admin_site.admin_view(self.vista_exportar_miskito_excel),
                name='codiselu_ciudad_exportar_miskito_excel'
            ),
        ]
        return custom_urls + urls

    def vista_exportar_miskito_pdf(self, request):
        solo_pend = request.GET.get('solo_pendientes', '1').lower() not in ('0', 'false', 'no')
        orientacion = request.GET.get('orientacion', request.GET.get('formato', 'vertical')).lower()
        if request.GET.get('horizontal', '').lower() in ('1', 'true', 'yes'):
            orientacion = 'horizontal'

        es_horiz = orientacion in ('horizontal', 'landscape', 'h')
        pdf_buffer = generar_pdf_traduccion_miskito(solo_pendientes=solo_pend, orientacion=orientacion)
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        sufijo_orient = "_Horizontal" if es_horiz else ""
        sufijo_modo = "Pendientes" if solo_pend else "Completo"
        nombre_archivo = f"Codice_Documentacion_Miskito_{sufijo_modo}{sufijo_orient}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response

    def vista_exportar_miskito_excel(self, request):
        solo_pend = request.GET.get('solo_pendientes', '1').lower() not in ('0', 'false', 'no')
        excel_buffer = generar_excel_traduccion_miskito(solo_pendientes=solo_pend)
        response = FileResponse(
            excel_buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        sufijo_modo = "Pendientes" if solo_pend else "Completo"
        nombre_archivo = f"Codice_Plantilla_Miskito_{sufijo_modo}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response


@admin.register(CircuitoCreativo)
class CircuitoCreativoAdmin(OcultarTraduccionesAlCrearMixin, admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'distancia_km', 'duracion_estimada', 'dificultad')
    list_filter = ('ciudad', 'dificultad')
    search_fields = ('nombre', 'nombre_en', 'nombre_zh', 'nombre_miq', 'descripcion')
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
        ('Traducción al Miskito (Manual)', {
            'fields': ('nombre_miq', 'descripcion_miq'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PuntoInteres)
class PuntoInteresAdmin(OcultarTraduccionesAlCrearMixin, admin.ModelAdmin):
    list_display = ('orden', 'nombre', 'circuito', 'tipo')
    list_filter = ('tipo', 'circuito__ciudad')
    search_fields = ('nombre', 'nombre_en', 'nombre_zh', 'nombre_miq', 'descripcion')
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
        ('Traducción al Miskito (Manual)', {
            'fields': ('nombre_miq', 'descripcion_miq'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DatoHistorico)
class DatoHistoricoAdmin(OcultarTraduccionesAlCrearMixin, admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'epoca_o_ano', 'ciudad', 'punto_interes')
    list_filter = ('tipo', 'ciudad')
    search_fields = ('titulo', 'titulo_en', 'titulo_zh', 'titulo_miq', 'contenido')
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
        ('Traducción al Miskito (Manual)', {
            'fields': ('titulo_miq', 'contenido_miq'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GaleriaMultimedia)
class GaleriaMultimediaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'ciudad', 'punto_interes', 'evento', 'recurso_multimedia')
    list_filter = ('tipo', 'ciudad', 'evento')
    search_fields = ('titulo', 'ciudad__nombre', 'punto_interes__nombre', 'evento__titulo')
    fields = ('ciudad', 'punto_interes', 'evento', 'titulo', 'tipo', 'imagen', 'video_archivo', 'video_url')

    def recurso_multimedia(self, obj):
        if obj.tipo == 'Imagen':
            return "✓ Imagen subida" if obj.imagen else "Sin archivo"
        if obj.video_archivo:
            return "✓ Video subido"
        if obj.video_url:
            return f"✓ URL ({obj.video_url[:30]}...)" if len(obj.video_url) > 30 else f"✓ URL ({obj.video_url})"
        return "Sin recurso"
    recurso_multimedia.short_description = "Recurso"


@admin.register(UsuarioPuntoVisitado)
class UsuarioPuntoVisitadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'punto_interes', 'es_validada', 'distancia_metros', 'fecha_visita')
    list_filter = ('es_validada', 'fecha_visita', 'usuario', 'punto_interes__circuito__ciudad')
    search_fields = ('usuario__username', 'punto_interes__nombre')
    readonly_fields = ('es_validada', 'distancia_metros')


class OportunidadInversionInline(admin.TabularInline):
    model = OportunidadInversion
    extra = 1

    def get_fields(self, request, obj=None):
        if obj is None:
            return (
                'titulo', 'descripcion', 'monto_requerido',
                'monto_minimo_inversion', 'monto_recaudado', 'retorno_estimado',
                'tipo_inversor_permitido', 'esta_activa'
            )
        return (
            'titulo', 'titulo_en', 'titulo_zh', 'titulo_miq',
            'descripcion', 'descripcion_en', 'descripcion_zh', 'descripcion_miq',
            'monto_requerido', 'monto_minimo_inversion', 'monto_recaudado',
            'retorno_estimado', 'tipo_inversor_permitido', 'esta_activa'
        )


class EmpresaMiembroInline(admin.TabularInline):
    model = EmpresaMiembro
    extra = 1
    autocomplete_fields = ['usuario']


@admin.register(Empresa)
class EmpresaAdmin(OcultarTraduccionesAlCrearMixin, admin.ModelAdmin):
    list_display = ('id', 'nombre', 'usuario', 'categoria', 'ciudad', 'numero_whatsapp', 'tiene_publicidad', 'acepta_inversiones', 'fecha_creacion')
    list_filter = ('tiene_publicidad', 'acepta_inversiones', 'categoria', 'ciudad')
    search_fields = ('nombre', 'nombre_en', 'nombre_zh', 'descripcion', 'usuario__username', 'numero_whatsapp')
    filter_horizontal = ('circuitos',)
    inlines = [EmpresaMiembroInline, OportunidadInversionInline]
    fieldsets = (
        ('Información General (Español)', {
            'fields': (
                'usuario', 'ciudad', 'punto_interes', 'nombre', 'descripcion',
                'categoria', 'direccion', 'telefono_contacto', 'numero_whatsapp',
                'email_contacto', 'sitio_web', 'imagen_portada', 'latitud', 'longitud',
                'acepta_inversiones'
            )
        }),
        ('Pauta Publicitaria y Circuitos', {
            'fields': ('tiene_publicidad', 'fecha_fin_publicidad', 'circuitos'),
            'description': 'Configura si la empresa cuenta con patrocinio para ser destacada en circuitos turísticos.'
        }),
        ('Traducción al Inglés (Auto / Editable)', {
            'fields': ('nombre_en', 'descripcion_en'),
            'classes': ('collapse',)
        }),
        ('Traducción al Mandarín (Auto / Editable)', {
            'fields': ('nombre_zh', 'descripcion_zh'),
            'classes': ('collapse',)
        }),
        ('Traducción al Miskito (Manual)', {
            'fields': ('nombre_miq', 'descripcion_miq'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OportunidadInversion)
class OportunidadInversionAdmin(OcultarTraduccionesAlCrearMixin, admin.ModelAdmin):
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
        ('Traducción al Miskito (Manual)', {
            'fields': ('titulo_miq', 'descripcion_miq'),
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
class EventoAdmin(OcultarTraduccionesAlCrearMixin, admin.ModelAdmin):
    list_display = ('id', 'titulo', 'creador', 'empresa', 'ciudad', 'fecha_inicio', 'solo_este_ano', 'total_granos_cafe', 'total_asistentes', 'es_oficial', 'esta_activo')
    list_filter = ('es_oficial', 'solo_este_ano', 'esta_activo', 'es_gratuito', 'ciudad', 'fecha_inicio')
    search_fields = ('titulo', 'titulo_en', 'titulo_zh', 'descripcion', 'rango_celebracion', 'ubicacion', 'creador__username', 'empresa__nombre')
    inlines = [GaleriaMultimediaInline, EventoAsistenciaInline]
    fieldsets = (
        ('Información General (Español)', {
            'fields': (
                'creador', 'empresa', 'ciudad', 'titulo', 'descripcion',
                'solo_este_ano', 'rango_celebracion',
                'fecha_inicio', 'fecha_fin', 'ubicacion', 'latitud', 'longitud',
                'imagen', 'precio_entrada', 'es_gratuito', 'cupo_maximo',
                'es_oficial', 'dias_previos_mural', 'esta_activo'
            )
        }),
        ('Traducción al Inglés (Auto / Editable)', {
            'fields': ('titulo_en', 'descripcion_en', 'rango_celebracion_en'),
            'classes': ('collapse',)
        }),
        ('Traducción al Mandarín (Auto / Editable)', {
            'fields': ('titulo_zh', 'descripcion_zh', 'rango_celebracion_zh'),
            'classes': ('collapse',)
        }),
        ('Traducción al Miskito (Manual)', {
            'fields': ('titulo_miq', 'descripcion_miq', 'rango_celebracion_miq'),
            'classes': ('collapse',)
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'creador' in form.base_fields:
            if obj is None and getattr(request, 'user', None) and request.user.is_authenticated:
                form.base_fields['creador'].initial = request.user
            form.base_fields['creador'].disabled = True
        return form

    def save_model(self, request, obj, form, change):
        if not change or not obj.creador_id:
            if getattr(request, 'user', None) and request.user.is_authenticated:
                obj.creador = request.user
        super().save_model(request, obj, form, change)


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


@admin.register(EmpresaMiembro)
class EmpresaMiembroAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'empresa', 'rol', 'fecha_incorporacion')
    list_filter = ('rol', 'fecha_incorporacion')
    search_fields = ('usuario__username', 'usuario__email', 'empresa__nombre')


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'autor', 'creado_por', 'tipo_autor', 'titulo', 'empresa', 'ciudad', 'evento', 'total_likes', 'total_comentarios', 'esta_activa', 'fecha_creacion')
    list_filter = ('tipo_autor', 'esta_activa', 'ciudad', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion', 'autor__username', 'creado_por__username', 'empresa__nombre')
    inlines = [PublicacionImagenInline, ComentarioPublicacionInline]


@admin.register(ComentarioPublicacion)
class ComentarioPublicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'autor', 'publicacion', 'contenido', 'esta_activo', 'fecha_creacion')
    list_filter = ('esta_activo', 'fecha_creacion')
    search_fields = ('contenido', 'autor__username', 'publicacion__titulo')





