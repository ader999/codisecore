import io
import os
from datetime import datetime
from django.conf import settings
from django.db.models import Prefetch

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    PageBreak,
    Image,
    HRFlowable
)
from reportlab.pdfgen import canvas

from .models import Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico, Evento


class NumberedCanvas(canvas.Canvas):
    """
    Canvas de doble pasada para calcular el total de páginas
    y añadir encabezados y pies de página dinámicos ('Página X de Y').
    Admite dinámicamente orientación vertical u horizontal según el tamaño configurado.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))

        page_w, page_h = self._pagesize

        # Encabezado (a partir de la página 2)
        if self._pageNumber > 1:
            self.drawString(36, page_h - 26, "Codice Lu • Guía Oficial para Traducción al Idioma Miskito (Miskitu)")
            self.setStrokeColor(colors.HexColor("#D1D5DB"))
            self.setLineWidth(0.5)
            self.line(36, page_h - 29, page_w - 36, page_h - 29)

        # Pie de página (todas las páginas)
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.5)
        self.line(36, 32, page_w - 36, 32)

        self.drawString(36, 22, "Codice Lu • Red Nacional de Ciudades Creativas de Nicaragua • Uso confidencial para traductores")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(page_w - 36, 22, page_str)

        self.restoreState()


def tiene_traduccion(valor) -> bool:
    """Verifica si un campo ya posee traducción al Miskito (no nulo y no en blanco)."""
    return bool(valor and str(valor).strip())


def crear_bloque_escritura_miskito(texto_traducido, prompt_guia, num_lineas=3, line_height=22, prompt_style=None, miskito_style=None, ancho_bloque=204):
    """
    Genera el contenido de la celda de traducción al Miskito.
    - Si el campo ya posee traducción registrada: muestra el texto traducido.
    - Si el campo está pendiente de traducción: genera renglones guía ('rayitas') claramente
      delimitados con altura ampliada (el doble del tamaño estándar para letra grande).
    - Admite ancho_bloque configurable para aprovechar la hoja horizontal.
    """
    if texto_traducido and str(texto_traducido).strip():
        return Paragraph(str(texto_traducido).strip(), miskito_style)

    filas = [[Paragraph(f"<i>{prompt_guia}</i>", prompt_style)]]
    for _ in range(num_lineas):
        filas.append([''])

    row_heights = [15] + [line_height] * num_lineas
    t = Table(filas, colWidths=[ancho_bloque], rowHeights=row_heights)
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEBELOW', (0, 1), (-1, -1), 0.65, colors.HexColor('#94A3B8')),
    ]))
    return t


def dividir_texto_en_bloques(texto, max_chars=450):
    """
    Divide un texto extenso en bloques manejables (< max_chars) respetando
    párrafos y oraciones para que ninguna celda de tabla exceda la altura
    imprimible de la página en ReportLab (evita LayoutError en hojas horizontales o verticales).
    """
    if not texto:
        return []
    texto_limpio = str(texto).replace('<br/>', '\n').replace('<br>', '\n').strip()
    if len(texto_limpio) <= max_chars:
        return [texto_limpio]

    lineas = [p.strip() for p in texto_limpio.split('\n') if p.strip()]
    bloques = []

    for linea in lineas:
        if len(linea) <= max_chars:
            bloques.append(linea)
        else:
            oraciones = [o.strip() for o in linea.split('. ') if o.strip()]
            chunk_actual = ""
            for o in oraciones:
                o_con_punto = o if o.endswith('.') else (o + '.')
                if not chunk_actual:
                    chunk_actual = o_con_punto
                elif len(chunk_actual) + 1 + len(o_con_punto) <= max_chars:
                    chunk_actual += " " + o_con_punto
                else:
                    bloques.append(chunk_actual)
                    chunk_actual = o_con_punto
            if chunk_actual:
                bloques.append(chunk_actual)

    bloques_finales = []
    for b in bloques:
        if len(b) <= max_chars * 1.25:
            bloques_finales.append(b)
        else:
            palabras = b.split(' ')
            cur = ""
            for pal in palabras:
                if not cur:
                    cur = pal
                elif len(cur) + 1 + len(pal) <= max_chars:
                    cur += " " + pal
                else:
                    bloques_finales.append(cur)
                    cur = pal
            if cur:
                bloques_finales.append(cur)

    return bloques_finales or [texto_limpio]


def obtener_estadisticas_traduccion_miskito():
    """
    Devuelve un diccionario con el recuento total y pendiente de traducción al Miskito
    para ciudades con circuitos, circuitos creativos y puntos de interés.
    """
    ciudades = Ciudad.objects.filter(circuitos__isnull=False).distinct().prefetch_related(
        Prefetch('circuitos', queryset=CircuitoCreativo.objects.prefetch_related(
            Prefetch('puntos_interes', queryset=PuntoInteres.objects.prefetch_related('datos_historicos'))
        )),
        Prefetch('eventos', queryset=Evento.objects.filter(esta_activo=True).order_by('fecha_inicio')),
        'datos_historicos'
    )

    total_campos = 0
    campos_pendientes = 0
    ciudades_pendientes = 0
    circuitos_pendientes = 0
    puntos_pendientes = 0
    eventos_pendientes = 0

    for c in ciudades:
        c_tiene_pend = False
        # Ciudad nombre y descripcion
        total_campos += 2
        if not tiene_traduccion(c.nombre_miq):
            campos_pendientes += 1
            c_tiene_pend = True
        if not tiene_traduccion(c.descripcion_miq):
            campos_pendientes += 1
            c_tiene_pend = True

        for dh in c.datos_historicos.filter(punto_interes__isnull=True):
            total_campos += 2
            if not tiene_traduccion(dh.titulo_miq):
                campos_pendientes += 1
                c_tiene_pend = True
            if not tiene_traduccion(dh.contenido_miq):
                campos_pendientes += 1
                c_tiene_pend = True

        for ev in c.eventos.all():
            ev_tiene_pend = False
            total_campos += 2
            if not tiene_traduccion(ev.titulo_miq):
                campos_pendientes += 1
                ev_tiene_pend = True
            if not tiene_traduccion(ev.descripcion_miq):
                campos_pendientes += 1
                ev_tiene_pend = True
            if ev.rango_celebracion:
                total_campos += 1
                if not tiene_traduccion(ev.rango_celebracion_miq):
                    campos_pendientes += 1
                    ev_tiene_pend = True
            if ev_tiene_pend:
                eventos_pendientes += 1
                c_tiene_pend = True

        for cir in c.circuitos.all():
            cir_tiene_pend = False
            total_campos += 2
            if not tiene_traduccion(cir.nombre_miq):
                campos_pendientes += 1
                cir_tiene_pend = True
            if not tiene_traduccion(cir.descripcion_miq):
                campos_pendientes += 1
                cir_tiene_pend = True

            for p in cir.puntos_interes.all():
                p_tiene_pend = False
                total_campos += 2
                if not tiene_traduccion(p.nombre_miq):
                    campos_pendientes += 1
                    p_tiene_pend = True
                if not tiene_traduccion(p.descripcion_miq):
                    campos_pendientes += 1
                    p_tiene_pend = True

                for dh_p in p.datos_historicos.all():
                    total_campos += 2
                    if not tiene_traduccion(dh_p.titulo_miq):
                        campos_pendientes += 1
                        p_tiene_pend = True
                    if not tiene_traduccion(dh_p.contenido_miq):
                        campos_pendientes += 1
                        p_tiene_pend = True

                if p_tiene_pend:
                    puntos_pendientes += 1
                    cir_tiene_pend = True

            if cir_tiene_pend:
                circuitos_pendientes += 1
                c_tiene_pend = True

        if c_tiene_pend:
            ciudades_pendientes += 1

    return {
        'total_ciudades_con_circuitos': ciudades.count(),
        'ciudades_pendientes': ciudades_pendientes,
        'circuitos_pendientes': circuitos_pendientes,
        'puntos_pendientes': puntos_pendientes,
        'eventos_pendientes': eventos_pendientes,
        'total_campos': total_campos,
        'campos_pendientes': campos_pendientes,
        'campos_traducidos': total_campos - campos_pendientes,
        'porcentaje_completado': round(((total_campos - campos_pendientes) / total_campos * 100), 1) if total_campos > 0 else 100.0
    }


def generar_pdf_traduccion_miskito(ciudades_ids=None, buffer_destino=None, solo_pendientes: bool = True, orientacion: str = 'vertical') -> io.BytesIO:
    """
    Genera un documento PDF estructurado y visualmente claro para que traductores
    puedan traducir los contenidos de Ciudades, Circuitos Creativos, Puntos de Interés
    y Eventos Culturales al idioma Miskito (Miskitu).

    Reglas de negocio aplicadas:
    - Excluye ciudades que no tengan circuitos creativos.
    - Incluye eventos culturales de las ciudades seleccionadas y eventos generales.
    - Si solo_pendientes=True (por defecto):
      * Omite campos que ya posean traducción al Miskito.
      * Omite puntos, circuitos, eventos y ciudades que ya estén completamente traducidos.
    - Soporta orientación vertical ('vertical') u horizontal ('horizontal' / 'landscape').
      En modo horizontal, la columna de traducción al Miskito se amplía sustancialmente
      (400 pt, más del 55% del ancho imprimible) para que el traductor disponga del máximo
      espacio para escribir con holgura.
    - Al final del documento se incluye un campo formal de reconocimiento y agradecimiento
      por el valioso tiempo consagrado a la traducción, culminando con '¡Tingki pali!' en Miskito.
    - Proporciona contexto cultural, explicación de cada elemento y su función.
    - Incluye identificadores de referencia [REF] para facilitar la carga posterior al sistema.
    """
    if buffer_destino is None:
        buffer_destino = io.BytesIO()

    # Filtrar solo ciudades que tengan circuitos creativos
    queryset = Ciudad.objects.filter(circuitos__isnull=False).distinct()
    if ciudades_ids:
        queryset = queryset.filter(id__in=ciudades_ids)

    queryset = queryset.prefetch_related(
        Prefetch(
            'circuitos',
            queryset=CircuitoCreativo.objects.prefetch_related(
                Prefetch(
                    'puntos_interes',
                    queryset=PuntoInteres.objects.prefetch_related('datos_historicos').order_by('orden')
                )
            ).order_by('nombre')
        ),
        Prefetch(
            'eventos',
            queryset=Evento.objects.filter(esta_activo=True).order_by('fecha_inicio')
        ),
        'datos_historicos'
    ).order_by('nombre')

    ciudades = list(queryset)

    # Procesar y filtrar según solo_pendientes
    ciudades_procesadas = []
    conteo_campos_pendientes = 0
    conteo_campos_omitidos = 0

    for ciudad in ciudades:
        c_nombre_pend = not tiene_traduccion(ciudad.nombre_miq)
        c_desc_pend = not tiene_traduccion(ciudad.descripcion_miq)

        if c_nombre_pend:
            conteo_campos_pendientes += 1
        else:
            conteo_campos_omitidos += 1

        if c_desc_pend:
            conteo_campos_pendientes += 1
        else:
            conteo_campos_omitidos += 1

        dh_ciudad_items = []
        for dh in ciudad.datos_historicos.filter(punto_interes__isnull=True):
            dh_tit_pend = not tiene_traduccion(dh.titulo_miq)
            dh_cont_pend = not tiene_traduccion(dh.contenido_miq)

            if dh_tit_pend: conteo_campos_pendientes += 1
            else: conteo_campos_omitidos += 1

            if dh_cont_pend: conteo_campos_pendientes += 1
            else: conteo_campos_omitidos += 1

            if not solo_pendientes or (dh_tit_pend or dh_cont_pend):
                dh_ciudad_items.append({
                    'objeto': dh,
                    'titulo_pendiente': dh_tit_pend,
                    'contenido_pendiente': dh_cont_pend
                })

        circuitos_items = []
        for cir in ciudad.circuitos.all():
            cir_nom_pend = not tiene_traduccion(cir.nombre_miq)
            cir_desc_pend = not tiene_traduccion(cir.descripcion_miq)

            if cir_nom_pend: conteo_campos_pendientes += 1
            else: conteo_campos_omitidos += 1

            if cir_desc_pend: conteo_campos_pendientes += 1
            else: conteo_campos_omitidos += 1

            puntos_items = []
            for p in cir.puntos_interes.all():
                p_nom_pend = not tiene_traduccion(p.nombre_miq)
                p_desc_pend = not tiene_traduccion(p.descripcion_miq)

                if p_nom_pend: conteo_campos_pendientes += 1
                else: conteo_campos_omitidos += 1

                if p_desc_pend: conteo_campos_pendientes += 1
                else: conteo_campos_omitidos += 1

                dh_punto_items = []
                for dh_p in p.datos_historicos.all():
                    dh_p_tit_pend = not tiene_traduccion(dh_p.titulo_miq)
                    dh_p_cont_pend = not tiene_traduccion(dh_p.contenido_miq)

                    if dh_p_tit_pend: conteo_campos_pendientes += 1
                    else: conteo_campos_omitidos += 1

                    if dh_p_cont_pend: conteo_campos_pendientes += 1
                    else: conteo_campos_omitidos += 1

                    if not solo_pendientes or (dh_p_tit_pend or dh_p_cont_pend):
                        dh_punto_items.append({
                            'objeto': dh_p,
                            'titulo_pendiente': dh_p_tit_pend,
                            'contenido_pendiente': dh_p_cont_pend
                        })

                p_tiene_pendientes = p_nom_pend or p_desc_pend or len(dh_punto_items) > 0
                if not solo_pendientes or p_tiene_pendientes:
                    puntos_items.append({
                        'objeto': p,
                        'nombre_pendiente': p_nom_pend,
                        'descripcion_pendiente': p_desc_pend,
                        'datos_historicos': dh_punto_items
                    })

            cir_tiene_pendientes = cir_nom_pend or cir_desc_pend or len(puntos_items) > 0
            if not solo_pendientes or cir_tiene_pendientes:
                circuitos_items.append({
                    'objeto': cir,
                    'nombre_pendiente': cir_nom_pend,
                    'descripcion_pendiente': cir_desc_pend,
                    'puntos': puntos_items
                })

        eventos_items = []
        for ev in ciudad.eventos.all():
            ev_tit_pend = not tiene_traduccion(ev.titulo_miq)
            ev_desc_pend = not tiene_traduccion(ev.descripcion_miq)
            ev_rango_pend = bool(ev.rango_celebracion and not tiene_traduccion(ev.rango_celebracion_miq))

            if ev_tit_pend: conteo_campos_pendientes += 1
            else: conteo_campos_omitidos += 1

            if ev_desc_pend: conteo_campos_pendientes += 1
            else: conteo_campos_omitidos += 1

            if ev.rango_celebracion:
                if ev_rango_pend: conteo_campos_pendientes += 1
                else: conteo_campos_omitidos += 1

            ev_tiene_pend = ev_tit_pend or ev_desc_pend or ev_rango_pend
            if not solo_pendientes or ev_tiene_pend:
                eventos_items.append({
                    'objeto': ev,
                    'titulo_pendiente': ev_tit_pend,
                    'descripcion_pendiente': ev_desc_pend,
                    'rango_pendiente': ev_rango_pend
                })

        c_tiene_pendientes = (
            c_nombre_pend or c_desc_pend or
            len(dh_ciudad_items) > 0 or
            len(circuitos_items) > 0 or
            len(eventos_items) > 0
        )
        if not solo_pendientes or c_tiene_pendientes:
            ciudades_procesadas.append({
                'objeto': ciudad,
                'nombre_pendiente': c_nombre_pend,
                'descripcion_pendiente': c_desc_pend,
                'datos_historicos': dh_ciudad_items,
                'circuitos': circuitos_items,
                'eventos': eventos_items
            })

    # Procesar eventos generales que no pertenecen a una ciudad específica
    eventos_generales_items = []
    for ev_g in Evento.objects.filter(ciudad__isnull=True, esta_activo=True).order_by('fecha_inicio'):
        ev_g_tit_pend = not tiene_traduccion(ev_g.titulo_miq)
        ev_g_desc_pend = not tiene_traduccion(ev_g.descripcion_miq)
        ev_g_rango_pend = bool(ev_g.rango_celebracion and not tiene_traduccion(ev_g.rango_celebracion_miq))

        if ev_g_tit_pend: conteo_campos_pendientes += 1
        else: conteo_campos_omitidos += 1

        if ev_g_desc_pend: conteo_campos_pendientes += 1
        else: conteo_campos_omitidos += 1

        if ev_g.rango_celebracion:
            if ev_g_rango_pend: conteo_campos_pendientes += 1
            else: conteo_campos_omitidos += 1

        if not solo_pendientes or (ev_g_tit_pend or ev_g_desc_pend or ev_g_rango_pend):
            eventos_generales_items.append({
                'objeto': ev_g,
                'titulo_pendiente': ev_g_tit_pend,
                'descripcion_pendiente': ev_g_desc_pend,
                'rango_pendiente': ev_g_rango_pend
            })

    # Configuración de orientación y página
    es_horizontal = str(orientacion).lower() in ('horizontal', 'landscape', 'h')
    tamano_pagina = landscape(letter) if es_horizontal else letter
    ancho_imprimible = 720 if es_horizontal else 540

    # Configuración de anchos según orientación:
    # En horizontal, la columna Miskito (400pt) es mucho más grande que las otras dos (130pt y 190pt),
    # abarcando el 55.5% del ancho de la página para proveer la máxima holgura de escritura manual.
    if es_horizontal:
        col_widths_traduccion = [130, 190, 400]
        ancho_miskito_bloque = 388
        col_widths_ciudad_banner = [460, 260]
        col_widths_eventos_banner = [460, 260]
        col_widths_circuito_banner = [450, 270]
        col_widths_gral_banner = [460, 260]
        col_widths_header = [2.2 * inch, 7.8 * inch]
        col_widths_resumen = [180, 180, 180, 180]
        col_widths_indice = [120, 70, 70, 70, 390]
    else:
        col_widths_traduccion = [120, 210, 210]
        ancho_miskito_bloque = 204
        col_widths_ciudad_banner = [330, 210]
        col_widths_eventos_banner = [340, 200]
        col_widths_circuito_banner = [320, 220]
        col_widths_gral_banner = [350, 190]
        col_widths_header = [2.2 * inch, 5.3 * inch]
        col_widths_resumen = [135, 135, 135, 135]
        col_widths_indice = [95, 65, 65, 65, 250]

    doc = SimpleDocTemplate(
        buffer_destino,
        pagesize=tamano_pagina,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Definir paleta de estilos tipográficos
    primary_color = colors.HexColor("#1E3A8A")     # Azul institucional Codice
    secondary_color = colors.HexColor("#92400E")   # Dorado/Ámbar cultural
    event_color = colors.HexColor("#6D28D9")       # Púrpura festivo / celebraciones y tradiciones
    neutral_dark = colors.HexColor("#1F2937")      # Gris oscuro para lectura
    neutral_light = colors.HexColor("#F3F4F6")     # Fondo suave
    border_color = colors.HexColor("#D1D5DB")
    accent_green = colors.HexColor("#065F46")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=primary_color,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=8
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=14.5,
        textColor=primary_color,
        spaceAfter=4
    )

    context_body_style = ParagraphStyle(
        'ContextBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.0,
        leading=9.3,
        textColor=neutral_dark
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    col_meta_style = ParagraphStyle(
        'ColMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=primary_color
    )

    col_spanish_style = ParagraphStyle(
        'ColSpanish',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=neutral_dark
    )

    col_miskito_style = ParagraphStyle(
        'ColMiskito',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11.5,
        textColor=accent_green
    )

    col_write_prompt_style = ParagraphStyle(
        'ColWritePrompt',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#9CA3AF")
    )

    badge_pending_style = ParagraphStyle(
        'BadgePending',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#DC2626")
    )

    def _bloque_miskito(texto, prompt, num_lineas=3, line_height=22):
        return crear_bloque_escritura_miskito(
            texto_traducido=texto,
            prompt_guia=prompt,
            num_lineas=num_lineas,
            line_height=line_height,
            prompt_style=col_write_prompt_style,
            miskito_style=col_miskito_style,
            ancho_bloque=ancho_miskito_bloque
        )

    def _agregar_filas_texto_extenso(
        filas_destino,
        titulo_campo,
        subtitulo_campo,
        ref_id,
        es_pendiente,
        texto_original,
        texto_traducido,
        prompt_guia,
        color_subtitulo="#92400E",
        max_chars=450
    ):
        texto_orig_limpio = (texto_original or "").strip()
        if not texto_orig_limpio:
            filas_destino.append([
                Paragraph(f"<b>{titulo_campo}</b><br/>"
                          f"<font size=7 color='#6B7280'>[REF: {ref_id}]</font><br/>"
                          f"{f'<font size=6.5 color=\"{color_subtitulo}\">{subtitulo_campo}</font><br/>' if subtitulo_campo else ''}"
                          f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if es_pendiente else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                Paragraph("<i>Sin descripción registrada</i>", col_spanish_style),
                _bloque_miskito(texto_traducido, prompt_guia, num_lineas=3, line_height=22)
            ])
            return

        bloques_es = dividir_texto_en_bloques(texto_orig_limpio, max_chars=max_chars)
        total_partes = len(bloques_es)

        if total_partes <= 1:
            lineas = 7 if len(texto_orig_limpio) > 220 else 5
            filas_destino.append([
                Paragraph(f"<b>{titulo_campo}</b><br/>"
                          f"<font size=7 color='#6B7280'>[REF: {ref_id}]</font><br/>"
                          f"{f'<font size=6.5 color=\"{color_subtitulo}\">{subtitulo_campo}</font><br/>' if subtitulo_campo else ''}"
                          f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if es_pendiente else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                Paragraph(texto_orig_limpio, col_spanish_style),
                _bloque_miskito(texto_traducido, prompt_guia, num_lineas=lineas, line_height=22)
            ])
        else:
            bloques_miq = dividir_texto_en_bloques(str(texto_traducido).strip(), max_chars=max_chars) if (texto_traducido and str(texto_traducido).strip()) else []

            for i, b_es in enumerate(bloques_es):
                num_parte = f"(Parte {i+1}/{total_partes})"
                ref_parte = f"{ref_id}:p{i+1}"
                if bloques_miq:
                    val_miq = bloques_miq[i] if i < len(bloques_miq) else "(Traducción en parte anterior)"
                else:
                    val_miq = None

                lineas = 6 if len(b_es) > 220 else 5
                prompt_p = prompt_guia.replace(" ]", f" {num_parte} ]") if " ]" in prompt_guia else f"{prompt_guia} {num_parte}"

                filas_destino.append([
                    Paragraph(f"<b>{titulo_campo} {num_parte}</b><br/>"
                              f"<font size=7 color='#6B7280'>[REF: {ref_parte}]</font><br/>"
                              f"{f'<font size=6.5 color=\"{color_subtitulo}\">{subtitulo_campo}</font><br/>' if subtitulo_campo else ''}"
                              f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if es_pendiente else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                    Paragraph(b_es, col_spanish_style),
                    _bloque_miskito(val_miq, prompt_p, num_lineas=lineas, line_height=22)
                ])

    def _agregar_filas_dato_historico(
        filas_destino,
        dh,
        traduccion_dh,
        ref_id,
        subtitulo,
        color_subtitulo="#92400E",
        max_chars=450
    ):
        contenido_limpio = (dh.contenido or "").strip()
        bloques_dh = dividir_texto_en_bloques(contenido_limpio, max_chars=max_chars) if contenido_limpio else []
        total_partes = len(bloques_dh)

        if total_partes <= 1:
            lineas_dh = 7 if (contenido_limpio and len(contenido_limpio) > 220) else 6
            filas_destino.append([
                Paragraph(f"<b>Dato Histórico / Leyenda</b><br/>"
                          f"<font size=7 color='#6B7280'>[REF: {ref_id}]</font><br/>"
                          f"<font size=6.5 color='{color_subtitulo}'>{subtitulo}</font>", col_meta_style),
                Paragraph(f"<b>{dh.titulo}</b> ({dh.epoca_o_ano or 'Histórico'}):<br/>{contenido_limpio}", col_spanish_style),
                _bloque_miskito(traduccion_dh, "[ Traducción de título e historia al Miskito ]", num_lineas=lineas_dh, line_height=22)
            ])
        else:
            bloques_miq = dividir_texto_en_bloques(str(traduccion_dh).strip(), max_chars=max_chars) if (traduccion_dh and str(traduccion_dh).strip()) else []
            for i, b_dh in enumerate(bloques_dh):
                num_parte = f"(Parte {i+1}/{total_partes})"
                ref_parte = f"{ref_id}:p{i+1}"
                if bloques_miq:
                    val_miq = bloques_miq[i] if i < len(bloques_miq) else "(Traducción en parte anterior)"
                else:
                    val_miq = None

                lineas_dh = 6 if len(b_dh) > 220 else 5
                prompt_p = f"[ Traducción de historia al Miskito {num_parte} ]"
                titulo_prefijo = f"<b>{dh.titulo}</b> ({dh.epoca_o_ano or 'Histórico'}):<br/>" if i == 0 else f"<b>{dh.titulo} ({num_parte})</b>:<br/>"

                filas_destino.append([
                    Paragraph(f"<b>Dato Histórico {num_parte}</b><br/>"
                              f"<font size=7 color='#6B7280'>[REF: {ref_parte}]</font><br/>"
                              f"<font size=6.5 color='{color_subtitulo}'>{subtitulo}</font>", col_meta_style),
                    Paragraph(f"{titulo_prefijo}{b_dh}", col_spanish_style),
                    _bloque_miskito(val_miq, prompt_p, num_lineas=lineas_dh, line_height=22)
                ])

    def _generar_bloque_agradecimiento():
        agradecimiento_estilo_titulo = ParagraphStyle(
            'AgradecimientoTitulo',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11.5,
            leading=14.5,
            textColor=colors.HexColor("#1E3A8A"),
            alignment=1
        )
        agradecimiento_estilo_texto = ParagraphStyle(
            'AgradecimientoTexto',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11.5,
            textColor=neutral_dark,
            alignment=4
        )
        agradecimiento_estilo_miskito = ParagraphStyle(
            'AgradecimientoMiskito',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#065F46"),
            alignment=1
        )
        agradecimiento_submiskito = ParagraphStyle(
            'AgradecimientoSubMiskito',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#4B5563"),
            alignment=1
        )
        meta_traductor_style = ParagraphStyle(
            'MetaTraductor',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=10.5,
            textColor=neutral_dark
        )

        texto_agradecimiento_html = (
            "<b>Apreciamos sinceramente el valioso tiempo, esfuerzo, conocimiento y dedicación que han consagrado a la traducción "
            "de este documento al idioma Miskito (Miskitu bil).</b><br/><br/>"
            "Su labor como traductores comunitarios no solo permite que las familias, estudiantes y visitantes hablantes de Miskito "
            "accedan plenamente en su propia lengua originaria a la riqueza patrimonial, artística y turística de la "
            "<b>Red Nacional de Ciudades Creativas de Nicaragua</b>, sino que representa un aporte invaluable para la salvaguarda, "
            "dignificación y revitalización de nuestro patrimonio lingüístico ancestral frente a las nuevas tecnologías."
        )

        ancho_interior = ancho_imprimible - 32
        tabla_registro_data = [
            [
                Paragraph("<b>Nombre del Traductor(a):</b> ____________________________________", meta_traductor_style),
                Paragraph("<b>Comunidad / Territorio:</b> ____________________________________", meta_traductor_style)
            ],
            [
                Paragraph("<b>Fecha de Traducción:</b> _____ / _____ / 202____", meta_traductor_style),
                Paragraph("<b>Firma / Aprobación:</b> ________________________________________", meta_traductor_style)
            ]
        ]
        t_reg = Table(tabla_registro_data, colWidths=[ancho_interior * 0.5, ancho_interior * 0.5])
        t_reg.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        bloque_contenido = [
            [Paragraph("🤝 <b>RECONOCIMIENTO Y AGRADECIMIENTO AL EQUIPO TRADUCTOR</b>", agradecimiento_estilo_titulo)],
            [Spacer(1, 3)],
            [Paragraph(texto_agradecimiento_html, agradecimiento_estilo_texto)],
            [Spacer(1, 3)],
            [t_reg],
            [Spacer(1, 5)],
            [Paragraph("¡TINGKI PALI!", agradecimiento_estilo_miskito)],
            [Paragraph("Tingki • <i>(Muchas gracias en idioma Miskito / Miskitu bil)</i>", agradecimiento_submiskito)]
        ]

        t_agrad = Table(bloque_contenido, colWidths=[ancho_imprimible])
        t_agrad.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
            ('BOX', (0, 0), (-1, -1), 1.2, colors.HexColor("#10B981")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, -2), (-1, -1), 'CENTER'),
        ]))
        return KeepTogether([t_agrad])

    story = []

    # =========================================================================
    # PORTADA / ENCABEZADO Y GUÍA DE CONTEXTO PARA EL TRADUCTOR
    # =========================================================================

    logo_path = os.path.join(settings.BASE_DIR, 'logocodicelu.png')
    subtitulo_orientacion = " • Hoja Horizontal (Espacio Ampliado para Escritura)" if es_horizontal else ""
    subtitulo_modo = (
        f"<font color='#B45309'><b>[ MODO FILTRO: Únicamente contenidos pendientes de traducción{subtitulo_orientacion} ]</b></font><br/>"
        "<i>Los elementos que ya cuentan con traducción al Miskito han sido omitidos automáticamente de este documento.</i>"
        if solo_pendientes else
        f"<font color='#1E40AF'><b>[ MODO COMPLETO: Incluye todos los elementos{subtitulo_orientacion} ]</b></font>"
    )

    if os.path.exists(logo_path):
        img = Image(logo_path, width=1.75 * inch, height=0.75 * inch)
        header_table = Table(
            [[img, Paragraph("<b>Codice Lu • Red Nacional de Ciudades Creativas</b><br/>"
                             "<font size=13 color='#1E3A8A'><b>GUÍA OFICIAL DE TRADUCCIÓN AL IDIOMA MISKITO</b></font><br/>"
                             f"<font size=8.5 color='#4B5563'>{subtitulo_modo}</font>", title_style)]],
            colWidths=col_widths_header
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
    else:
        story.append(Paragraph("<b>Codice Lu • GUÍA OFICIAL DE TRADUCCIÓN AL IDIOMA MISKITO</b>", title_style))
        story.append(Paragraph(subtitulo_modo, subtitle_style))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=8, spaceBefore=0))

    # Resumen y métricas de pendientes
    total_cir_pend = sum(len(c['circuitos']) for c in ciudades_procesadas)
    total_pts_pend = sum(sum(len(cir['puntos']) for cir in c['circuitos']) for c in ciudades_procesadas)
    total_ev_pend = sum(len(c.get('eventos', [])) for c in ciudades_procesadas) + len(eventos_generales_items)
    fecha_hoy = datetime.now().strftime("%d de %B de %Y")

    resumen_data = [
        [
            Paragraph(f"<b>Fecha:</b> {fecha_hoy}", context_body_style),
            Paragraph(f"<b>Ciudades:</b> {len(ciudades_procesadas)}", context_body_style),
            Paragraph(f"<b>Circuitos:</b> {total_cir_pend}", context_body_style),
            Paragraph(f"<b>Paradas:</b> {total_pts_pend}", context_body_style),
        ],
        [
            Paragraph(f"<b>Eventos / Fiestas:</b> {total_ev_pend}", context_body_style),
            Paragraph(f"<b>Filtro activo:</b> {'Solo pendientes' if solo_pendientes else 'Todos'}", context_body_style),
            Paragraph(f"<b>Por traducir:</b> <font color='#DC2626'><b>{conteo_campos_pendientes}</b></font>", context_body_style),
            Paragraph(f"<b>Ya traducidos:</b> <font color='#059669'><b>{conteo_campos_omitidos}</b></font>", context_body_style),
        ]
    ]
    t_resumen = Table(resumen_data, colWidths=col_widths_resumen)
    t_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_resumen)
    story.append(Spacer(1, 5))

    # =========================================================================
    # RECUADRO DE CONTEXTO EXPLICATIVO PARA EL TRADUCTOR
    # =========================================================================
    contexto_html = (
        "<b>¿QUÉ ES LA PLATAFORMA CODICE (CODICE LU) Y CUÁL ES EL OBJETIVO DE ESTE DOCUMENTO?</b><br/>"
        "<b>Codice Lu</b> (cuya identidad visual integra el ideograma de ruta o camino) es la plataforma tecnológica oficial "
        "diseñada para articular, georreferenciar y difundir la riqueza patrimonial, cultural, artística, tradicional y productiva de la "
        "<b>Red Nacional de Ciudades Creativas de Nicaragua</b> (Estelí, León, Managua, Granada, Masaya, Nagarote, "
        "San Juan de Oriente, Juigalpa, Matagalpa y Bluefields). Mediante mapas interactivos, circuitos temáticos y una aplicación "
        "móvil comunitaria, Codice orienta a los visitantes en el reconocimiento de nuestros destinos e identidades creativas.<br/><br/>"
        "<b>OBJETIVO DE LA TRADUCCIÓN AL IDIOMA MISKITO (MISKITU BIL):</b><br/>"
        "Nicaragua es un país multiétnico, multicultural y multilingüe. El idioma <b>Miskito (Miskitu)</b> es la lengua originaria "
        "más hablada en la Costa Caribe nicaragüense (RACCN y RACCS). El objetivo primordial de esta traducción es garantizar la "
        "<b>inclusión lingüística y el acceso intercultural</b>, permitiendo que la población, familias y estudiantes hablantes de "
        "Miskito puedan disfrutar plenamente de la información turística y cultural en su propia lengua originaria, al mismo tiempo que se "
        "apoya la preservación digital, dignificación y revitalización del patrimonio lingüístico ancestral frente a las nuevas tecnologías.<br/><br/>"
        "<b>ESTRUCTURA Y SIGNIFICADO DE CADA ELEMENTO:</b><br/>"
        "• <b>Ciudad (Municipio):</b> Territorio sede de la Red de Ciudades Creativas. Su descripción presenta la identidad general, historia "
        "y vocación cultural. <i>(Se han excluido de este documento las ciudades que no cuentan con circuitos creativos registrados).</i><br/>"
        "• <b>Circuito Creativo (Ruta Temática):</b> Recorrido turístico planificado (peatonal o vehicular) que articula atractivos vinculados "
        "a murales, gastronomía tradicional, talleres artesanales o arquitectura.<br/>"
        "• <b>Punto de Interés (Parada o Hito):</b> Estaciones individuales que integran el circuito (museos, talleres, monumentos, "
        "miradores). Cada hito incluye su número de parada y categoría.<br/>"
        "• <b>Dato Histórico / Tradición:</b> Leyendas, crónicas, saberes populares o mitos tradicionales que otorgan valor inmaterial a cada sitio.<br/>"
        "• <b>Evento / Festividad Cultural:</b> Fiestas patronales, expresiones religiosas tradicionales y festivales folclóricos o artesanales "
        "(ej. La Gritería, Alfombras Pasionarias, festivales patronales). Incluye nombre, fechas y contexto.<br/><br/>"
        "<b>INSTRUCCIONES CLAVE PARA EL EQUIPO TRADUCTOR:</b><br/>"
        "1. <b>Filtro de Contenidos:</b> Este documento recopila únicamente aquellos textos que <b>aún no disponen de traducción registrada</b> en el sistema.<br/>"
        "2. <b>Fidelidad y Contexto Cultural:</b> Traduzca respetando el sentido cultural de la comunidad. Los nombres propios y topónimos "
        "(ej. 'Sutiaba', 'Monimbó', 'Tiscapa') se pueden conservar o adaptar según la fonética del Miskito.<br/>"
        "3. <b>Renglones de Escritura Ampliada:</b> Escriba la traducción directamente sobre las líneas guía de la columna <i>'Traducción al Miskito (Miskitu bil)'</i>, "
        "diseñadas con amplio espacio horizontal y vertical para permitir una caligrafía cómoda y clara.<br/>"
        "4. <b>Código Técnico de Referencia [REF: ...]:</b> Cada elemento posee un código identificador único (ej. <i>[REF: CIUDAD:14:nombre_miq]</i>), "
        "indispensable para registrar cada texto con absoluta precisión en la base de datos central sin margen de confusión."
    )

    t_contexto = Table([[Paragraph(contexto_html, context_body_style)]], colWidths=[ancho_imprimible])
    t_contexto.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1.2, colors.HexColor("#3B82F6")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_contexto)
    story.append(Spacer(1, 4))

    # CASO ESPECIAL: Todo el contenido ya está traducido
    if len(ciudades_procesadas) == 0 and len(eventos_generales_items) == 0:
        completado_html = (
            "<font size=16 color='#047857'><b>TRADUCCIÓN AL MISKITO COMPLETADA</b></font><br/><br/>"
            "<font size=11 color='#1F2937'>No se encontraron textos pendientes de traducción en las ciudades con circuitos creativos ni eventos.<br/>"
            "Todos los nombres, descripciones, festividades y puntos de interés ya cuentan con su equivalente en idioma Miskito (Miskitu bil).<br/><br/>"
            "Si deseas descargar la guía completa con todos los contenidos traducidos como respaldo o revisión, "
            "selecciona la opción <b>'Descargar Completo'</b> en el panel de control.</font>"
        )
        t_completado = Table([[Paragraph(completado_html, context_body_style)]], colWidths=[ancho_imprimible])
        t_completado.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#10B981")),
            ('TOPPADDING', (0, 0), (-1, -1), 18),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(t_completado)
        story.append(Spacer(1, 10))
        story.append(_generar_bloque_agradecimiento())
        doc.build(story, canvasmaker=NumberedCanvas)
        buffer_destino.seek(0)
        return buffer_destino

    # Índice de Ciudades con elementos pendientes
    story.append(Paragraph("<b>Índice de Elementos con Contenidos Pendientes de Traducción:</b>", section_header_style))
    tabla_indice_data = [
        [
            Paragraph("<b>Ciudad / Ámbito</b>", table_header_style),
            Paragraph("<b>Circuitos</b>", table_header_style),
            Paragraph("<b>Paradas</b>", table_header_style),
            Paragraph("<b>Eventos</b>", table_header_style),
            Paragraph("<b>Detalle de Contenidos</b>", table_header_style)
        ]
    ]
    for c_info in ciudades_procesadas:
        c = c_info['objeto']
        cirs_nombres = ", ".join([cir['objeto'].nombre for cir in c_info['circuitos']])
        evs_nombres = ", ".join([ev['objeto'].titulo for ev in c_info.get('eventos', [])])
        detalles_partes = []
        if cirs_nombres:
            detalles_partes.append(f"<b>Rutas:</b> {cirs_nombres}")
        if evs_nombres:
            detalles_partes.append(f"<b>Fiestas:</b> {evs_nombres}")
        detalle_texto = " • ".join(detalles_partes) or "Datos generales de la ciudad"

        pts_count = sum(len(cir['puntos']) for cir in c_info['circuitos'])
        tabla_indice_data.append([
            Paragraph(f"<b>{c.nombre}</b>", col_meta_style),
            Paragraph(f"{len(c_info['circuitos'])} ruta(s)", col_spanish_style),
            Paragraph(f"{pts_count} parada(s)", col_spanish_style),
            Paragraph(f"{len(c_info.get('eventos', []))} fiesta(s)", col_spanish_style),
            Paragraph(f"<font size=7 color='#4B5563'>{detalle_texto}</font>", col_spanish_style),
        ])

    if len(eventos_generales_items) > 0:
        evs_g_nombres = ", ".join([ev_g['objeto'].titulo for ev_g in eventos_generales_items])
        tabla_indice_data.append([
            Paragraph("<b>Nacional / General</b>", col_meta_style),
            Paragraph("—", col_spanish_style),
            Paragraph("—", col_spanish_style),
            Paragraph(f"{len(eventos_generales_items)} fiesta(s)", col_spanish_style),
            Paragraph(f"<font size=7 color='#4B5563'><b>Fiestas:</b> {evs_g_nombres}</font>", col_spanish_style),
        ])

    t_indice = Table(tabla_indice_data, colWidths=col_widths_indice)
    t_indice.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_indice)

    # Salto de página para que las tablas de traducción inicien en página limpia
    story.append(PageBreak())

    # =========================================================================
    # CUERPO PRINCIPAL: SECCIONES POR CIUDAD, CIRCUITO Y PUNTOS DE INTERÉS
    # =========================================================================

    for idx_c, c_info in enumerate(ciudades_procesadas):
        if idx_c > 0:
            story.append(PageBreak())

        ciudad = c_info['objeto']

        # Banner de Ciudad
        banner_ciudad = Table(
            [[
                Paragraph(f"<font size=12 color='white'><b>CIUDAD: {ciudad.nombre.upper()}</b></font>", table_header_style),
                Paragraph(f"<font size=8.5 color='#E0E7FF'><b>{len(c_info['circuitos'])} Circuitos con pendientes</b> • ID Sistema #{ciudad.id}</font>", ParagraphStyle('R', parent=table_header_style, alignment=2))
            ]],
            colWidths=col_widths_ciudad_banner
        )
        banner_ciudad.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), primary_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(banner_ciudad)
        story.append(Spacer(1, 4))

        # Filas de traducción de la Ciudad (solo las que falten si solo_pendientes=True)
        filas_ciudad = [
            [
                Paragraph("<b>Campo & Referencia</b>", table_header_style),
                Paragraph("<b>Texto Original en Español</b>", table_header_style),
                Paragraph("<b>Traducción al Miskito (Miskitu bil)</b>", table_header_style),
            ]
        ]

        if not solo_pendientes or c_info['nombre_pendiente']:
            filas_ciudad.append([
                Paragraph(f"<b>Nombre Ciudad</b><br/>"
                          f"<font size=7 color='#6B7280'>[REF: CIUDAD:{ciudad.id}:nombre_miq]</font><br/>"
                          f"<font size=6.5 color='#92400E'>Título del municipio</font><br/>"
                          f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if c_info['nombre_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                Paragraph(f"<b>{ciudad.nombre}</b>", col_spanish_style),
                _bloque_miskito(ciudad.nombre_miq, "[ Escribir nombre en Miskito ]", num_lineas=3, line_height=23)
            ])

        if not solo_pendientes or c_info['descripcion_pendiente']:
            _agregar_filas_texto_extenso(
                filas_destino=filas_ciudad,
                titulo_campo="Descripción Cultural",
                subtitulo_campo="Resumen general cultural",
                ref_id=f"CIUDAD:{ciudad.id}:descripcion_miq",
                es_pendiente=c_info['descripcion_pendiente'],
                texto_original=ciudad.descripcion,
                texto_traducido=ciudad.descripcion_miq,
                prompt_guia="[ Escribir traducción al Miskito de la descripción ]",
                color_subtitulo="#92400E"
            )

        # Datos Históricos generales de la ciudad
        for dh_dict in c_info['datos_historicos']:
            dh = dh_dict['objeto']
            traduccion_dh = (dh.titulo_miq + "<br/>" + dh.contenido_miq) if (dh.titulo_miq and dh.contenido_miq) else (dh.contenido_miq or dh.titulo_miq)
            _agregar_filas_dato_historico(
                filas_destino=filas_ciudad,
                dh=dh,
                traduccion_dh=traduccion_dh,
                ref_id=f"DATO:{dh.id}:titulo_miq & contenido_miq",
                subtitulo=f"Tipo: {dh.tipo}",
                color_subtitulo="#92400E"
            )

        if len(filas_ciudad) > 1:
            t_ciudad = Table(filas_ciudad, colWidths=col_widths_traduccion)
            t_ciudad.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
                ('BOX', (0, 0), (-1, -1), 1, border_color),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#F8FAFC")),
                ('BACKGROUND', (2, 1), (2, -1), colors.HexColor("#FEFCE8")),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(t_ciudad)
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("<font size=8.5 color='#059669'>✓ <i>Los datos generales de esta ciudad ya están completamente traducidos. A continuación se presentan las festividades, circuitos y paradas pendientes:</i></font>", subtitle_style))
            story.append(Spacer(1, 4))

        # =====================================================================
        # EVENTOS Y FESTIVIDADES CULTURALES DE LA CIUDAD
        # =====================================================================
        eventos_ciudad = c_info.get('eventos', [])
        if len(eventos_ciudad) > 0:
            story.append(Spacer(1, 4))
            banner_eventos = Table(
                [[
                    Paragraph(f"<font size=10 color='white'><b>EVENTOS Y FESTIVIDADES CULTURALES ({len(eventos_ciudad)} pendiente(s))</b></font>", table_header_style),
                    Paragraph(f"<font size=8 color='#DDD6FE'>Festividades de {ciudad.nombre}</font>", ParagraphStyle('EVR', parent=table_header_style, alignment=2))
                ]],
                colWidths=col_widths_eventos_banner
            )
            banner_eventos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), event_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(banner_eventos)
            story.append(Spacer(1, 2))

            for ev_info in eventos_ciudad:
                ev = ev_info['objeto']
                filas_evento = [
                    [
                        Paragraph("<b>Campo & Referencia</b>", table_header_style),
                        Paragraph("<b>Texto Original en Español</b>", table_header_style),
                        Paragraph("<b>Traducción al Miskito (Miskitu bil)</b>", table_header_style),
                    ]
                ]

                if not solo_pendientes or ev_info['titulo_pendiente']:
                    filas_evento.append([
                        Paragraph(f"<b>Nombre del Evento</b><br/>"
                                  f"<font size=7 color='#6B7280'>[REF: EVENTO:{ev.id}:titulo_miq]</font><br/>"
                                  f"<font size=6.5 color='#6D28D9'>Festividad cultural</font><br/>"
                                  f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if ev_info['titulo_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                        Paragraph(f"<b>{ev.titulo}</b>", col_spanish_style),
                        _bloque_miskito(ev.titulo_miq, "[ Escribir nombre del evento en Miskito ]", num_lineas=3, line_height=23)
                    ])

                if ev.rango_celebracion and (not solo_pendientes or ev_info['rango_pendiente']):
                    filas_evento.append([
                        Paragraph(f"<b>Fecha / Rango</b><br/>"
                                  f"<font size=7 color='#6B7280'>[REF: EVENTO:{ev.id}:rango_celebracion_miq]</font><br/>"
                                  f"<font size=6.5 color='#6D28D9'>Período tradicional de celebración</font><br/>"
                                  f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if ev_info['rango_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                        Paragraph(f"{ev.rango_celebracion}", col_spanish_style),
                        _bloque_miskito(ev.rango_celebracion_miq, "[ Escribir rango/fecha en Miskito ]", num_lineas=2, line_height=23)
                    ])

                if not solo_pendientes or ev_info['descripcion_pendiente']:
                    _agregar_filas_texto_extenso(
                        filas_destino=filas_evento,
                        titulo_campo="Descripción del Evento",
                        subtitulo_campo="Contexto de la festividad",
                        ref_id=f"EVENTO:{ev.id}:descripcion_miq",
                        es_pendiente=ev_info['descripcion_pendiente'],
                        texto_original=ev.descripcion,
                        texto_traducido=ev.descripcion_miq,
                        prompt_guia="[ Escribir traducción al Miskito de la festividad ]",
                        color_subtitulo="#6D28D9"
                    )

                if len(filas_evento) > 1:
                    t_evento = Table(filas_evento, colWidths=col_widths_traduccion)
                    t_evento.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#5B21B6")),
                        ('BOX', (0, 0), (-1, -1), 1, border_color),
                        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
                        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#F5F3FF")),
                        ('BACKGROUND', (2, 1), (2, -1), colors.HexColor("#FEFCE8")),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    story.append(t_evento)
                    story.append(Spacer(1, 4))

        # =====================================================================
        # CIRCUITOS CREATIVOS DENTRO DE LA CIUDAD
        # =====================================================================
        for idx_cir, cir_info in enumerate(c_info['circuitos']):
            circuito = cir_info['objeto']
            story.append(Spacer(1, 4))

            # Banner Circuito
            banner_circuito = Table(
                [[
                    Paragraph(f"<font size=10 color='white'><b>CIRCUITO CREATIVO: {circuito.nombre.upper()}</b></font>", table_header_style),
                    Paragraph(f"<font size=8 color='#FEF3C7'>Dificultad: {circuito.dificultad} • {circuito.distancia_km} km • {circuito.duracion_estimada} • ID #{circuito.id}</font>", ParagraphStyle('CR', parent=table_header_style, alignment=2))
                ]],
                colWidths=col_widths_circuito_banner
            )
            banner_circuito.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), secondary_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(banner_circuito)
            story.append(Spacer(1, 2))

            filas_circuito = [
                [
                    Paragraph("<b>Campo & Referencia</b>", table_header_style),
                    Paragraph("<b>Texto Original en Español</b>", table_header_style),
                    Paragraph("<b>Traducción al Miskito (Miskitu bil)</b>", table_header_style),
                ]
            ]

            if not solo_pendientes or cir_info['nombre_pendiente']:
                filas_circuito.append([
                    Paragraph(f"<b>Nombre del Circuito</b><br/>"
                              f"<font size=7 color='#6B7280'>[REF: CIRCUITO:{circuito.id}:nombre_miq]</font><br/>"
                              f"<font size=6.5 color='#92400E'>Nombre oficial del recorrido</font><br/>"
                              f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if cir_info['nombre_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                    Paragraph(f"<b>{circuito.nombre}</b>", col_spanish_style),
                    _bloque_miskito(circuito.nombre_miq, "[ Escribir nombre del circuito en Miskito ]", num_lineas=3, line_height=23)
                ])

            if not solo_pendientes or cir_info['descripcion_pendiente']:
                _agregar_filas_texto_extenso(
                    filas_destino=filas_circuito,
                    titulo_campo="Descripción del Recorrido",
                    subtitulo_campo="Contexto temático de la ruta",
                    ref_id=f"CIRCUITO:{circuito.id}:descripcion_miq",
                    es_pendiente=cir_info['descripcion_pendiente'],
                    texto_original=circuito.descripcion,
                    texto_traducido=circuito.descripcion_miq,
                    prompt_guia="[ Escribir descripción del circuito en Miskito ]",
                    color_subtitulo="#92400E"
                )

            if len(filas_circuito) > 1:
                t_circuito = Table(filas_circuito, colWidths=col_widths_traduccion)
                t_circuito.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#B45309")),
                    ('BOX', (0, 0), (-1, -1), 1, border_color),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
                    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#FFFBEB")),
                    ('BACKGROUND', (2, 1), (2, -1), colors.HexColor("#FEFCE8")),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(t_circuito)
                story.append(Spacer(1, 4))

            # -----------------------------------------------------------------
            # PUNTOS DE INTERÉS PENDIENTES DEL CIRCUITO
            # -----------------------------------------------------------------
            puntos_lista = cir_info['puntos']
            if len(puntos_lista) > 0:
                story.append(Paragraph(f"<b>Paradas del Circuito por Traducir ({len(puntos_lista)} pendiente(s)):</b>", section_header_style))

                for p_info in puntos_lista:
                    p = p_info['objeto']
                    filas_punto = []

                    if not solo_pendientes or p_info['nombre_pendiente']:
                        filas_punto.append([
                            Paragraph(f"<b>Parada #{p.orden}: {p.nombre}</b><br/>"
                                      f"<font size=7 color='#6B7280'>Categoría: {p.get_tipo_display()}<br/>[REF: PUNTO:{p.id}:nombre_miq]</font><br/>"
                                      f"{'<font size=6.5 color=\"#DC2626\">● Nombre pendiente</font>' if p_info['nombre_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                            Paragraph(f"<b>{p.nombre}</b>", col_spanish_style),
                            _bloque_miskito(p.nombre_miq, "[ Nombre del punto en Miskito ]", num_lineas=3, line_height=23)
                        ])

                    if not solo_pendientes or p_info['descripcion_pendiente']:
                        _agregar_filas_texto_extenso(
                            filas_destino=filas_punto,
                            titulo_campo="Descripción del Atractivo",
                            subtitulo_campo="Explicación de qué se hace o aprecia aquí",
                            ref_id=f"PUNTO:{p.id}:descripcion_miq",
                            es_pendiente=p_info['descripcion_pendiente'],
                            texto_original=p.descripcion,
                            texto_traducido=p.descripcion_miq,
                            prompt_guia="[ Traducción al Miskito del atractivo y actividades ]",
                            color_subtitulo="#0F766E"
                        )

                    # Datos históricos del punto
                    for dh_p_dict in p_info['datos_historicos']:
                        dh_p = dh_p_dict['objeto']
                        traduccion_dhp = (dh_p.titulo_miq + "<br/>" + dh_p.contenido_miq) if (dh_p.titulo_miq and dh_p.contenido_miq) else (dh_p.contenido_miq or dh_p.titulo_miq)
                        _agregar_filas_dato_historico(
                            filas_destino=filas_punto,
                            dh=dh_p,
                            traduccion_dh=traduccion_dhp,
                            ref_id=f"DATO:{dh_p.id}:titulo_miq & contenido_miq",
                            subtitulo=f"Tipo: {dh_p.tipo}",
                            color_subtitulo="#0F766E"
                        )

                    if len(filas_punto) > 0:
                        t_punto = Table(filas_punto, colWidths=col_widths_traduccion)
                        t_punto.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F0FDF4")),
                            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#FEFCE8")),
                            ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor("#86EFAC")),
                            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ]))
                        story.append(t_punto)
                        story.append(Spacer(1, 4))

            story.append(Spacer(1, 6))

    # =========================================================================
    # EVENTOS Y FESTIVIDADES GENERALES / NACIONALES (SIN CIUDAD ESPECÍFICA)
    # =========================================================================
    if len(eventos_generales_items) > 0:
        if len(ciudades_procesadas) > 0:
            story.append(PageBreak())

        banner_gral = Table(
            [[
                Paragraph("<font size=12 color='white'><b>EVENTOS Y FESTIVIDADES NACIONALES / GENERALES</b></font>", table_header_style),
                Paragraph(f"<font size=8.5 color='#DDD6FE'><b>{len(eventos_generales_items)} Eventos con pendientes</b></font>", ParagraphStyle('EVGR', parent=table_header_style, alignment=2))
            ]],
            colWidths=col_widths_gral_banner
        )
        banner_gral.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), event_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(banner_gral)
        story.append(Spacer(1, 6))

        for ev_g_info in eventos_generales_items:
            ev = ev_g_info['objeto']
            filas_ev_g = [
                [
                    Paragraph("<b>Campo & Referencia</b>", table_header_style),
                    Paragraph("<b>Texto Original en Español</b>", table_header_style),
                    Paragraph("<b>Traducción al Miskito (Miskitu bil)</b>", table_header_style),
                ]
            ]
            if not solo_pendientes or ev_g_info['titulo_pendiente']:
                filas_ev_g.append([
                    Paragraph(f"<b>Nombre del Evento</b><br/>"
                              f"<font size=7 color='#6B7280'>[REF: EVENTO:{ev.id}:titulo_miq]</font><br/>"
                              f"<font size=6.5 color='#6D28D9'>Festividad nacional o general</font><br/>"
                              f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if ev_g_info['titulo_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                    Paragraph(f"<b>{ev.titulo}</b>", col_spanish_style),
                    _bloque_miskito(ev.titulo_miq, "[ Escribir nombre del evento en Miskito ]", num_lineas=3, line_height=23)
                ])
            if ev.rango_celebracion and (not solo_pendientes or ev_g_info['rango_pendiente']):
                filas_ev_g.append([
                    Paragraph(f"<b>Fecha / Rango</b><br/>"
                              f"<font size=7 color='#6B7280'>[REF: EVENTO:{ev.id}:rango_celebracion_miq]</font><br/>"
                              f"<font size=6.5 color='#6D28D9'>Período tradicional de celebración</font><br/>"
                              f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if ev_g_info['rango_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                    Paragraph(f"{ev.rango_celebracion}", col_spanish_style),
                    _bloque_miskito(ev.rango_celebracion_miq, "[ Escribir rango/fecha en Miskito ]", num_lineas=2, line_height=23)
                ])
            if not solo_pendientes or ev_g_info['descripcion_pendiente']:
                _agregar_filas_texto_extenso(
                    filas_destino=filas_ev_g,
                    titulo_campo="Descripción del Evento",
                    subtitulo_campo="Contexto de la festividad",
                    ref_id=f"EVENTO:{ev.id}:descripcion_miq",
                    es_pendiente=ev_g_info['descripcion_pendiente'],
                    texto_original=ev.descripcion,
                    texto_traducido=ev.descripcion_miq,
                    prompt_guia="[ Escribir traducción al Miskito de la festividad ]",
                    color_subtitulo="#6D28D9"
                )

            if len(filas_ev_g) > 1:
                t_ev_g = Table(filas_ev_g, colWidths=col_widths_traduccion)
                t_ev_g.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#5B21B6")),
                    ('BOX', (0, 0), (-1, -1), 1, border_color),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
                    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#F5F3FF")),
                    ('BACKGROUND', (2, 1), (2, -1), colors.HexColor("#FEFCE8")),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(t_ev_g)
                story.append(Spacer(1, 4))

    # =========================================================================
    # RECONOCIMIENTO Y AGRADECIMIENTO AL EQUIPO TRADUCTOR
    # =========================================================================
    story.append(Spacer(1, 12))
    story.append(_generar_bloque_agradecimiento())

    # Construir documento PDF con NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer_destino.seek(0)
    return buffer_destino
