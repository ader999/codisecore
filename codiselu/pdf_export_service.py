import io
import os
from datetime import datetime
from django.conf import settings
from django.db.models import Prefetch

from reportlab.lib.pagesizes import letter
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

        # Encabezado (a partir de la página 2)
        if self._pageNumber > 1:
            self.drawString(36, 11 * inch - 26, "Codice路 • Guía de Contenidos para Traducción al Idioma Miskito (Miskitu)")
            self.setStrokeColor(colors.HexColor("#D1D5DB"))
            self.setLineWidth(0.5)
            self.line(36, 11 * inch - 29, 8.5 * inch - 36, 11 * inch - 29)

        # Pie de página (todas las páginas)
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.5)
        self.line(36, 32, 8.5 * inch - 36, 32)

        self.drawString(36, 22, "Codice路 • Plataforma de Turismo Creativo de Nicaragua • Uso confidencial para traductores")
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(8.5 * inch - 36, 22, page_str)

        self.restoreState()


def tiene_traduccion(valor) -> bool:
    """Verifica si un campo ya posee traducción al Miskito (no nulo y no en blanco)."""
    return bool(valor and str(valor).strip())


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


def generar_pdf_traduccion_miskito(ciudades_ids=None, buffer_destino=None, solo_pendientes: bool = True) -> io.BytesIO:
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

    # Configuración de página
    # Ancho imprimible: 8.5 * 72 - 72 = 540 puntos (márgenes de 0.5 pulgada / 36 pt)
    doc = SimpleDocTemplate(
        buffer_destino,
        pagesize=letter,
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
        fontSize=8.5,
        leading=11.5,
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

    story = []

    # =========================================================================
    # PORTADA / ENCABEZADO Y GUÍA DE CONTEXTO PARA EL TRADUCTOR
    # =========================================================================

    logo_path = os.path.join(settings.BASE_DIR, 'logocodicelu.png')
    subtitulo_modo = (
        "<font color='#B45309'><b>[ MODO FILTRO: Únicamente contenidos pendientes de traducción ]</b></font><br/>"
        "<i>Los elementos que ya cuentan con traducción al Miskito han sido omitidos automáticamente de este documento.</i>"
        if solo_pendientes else
        "<font color='#1E40AF'><b>[ MODO COMPLETO: Incluye todos los elementos ]</b></font>"
    )

    if os.path.exists(logo_path):
        img = Image(logo_path, width=2.0 * inch, height=0.9 * inch)
        header_table = Table(
            [[img, Paragraph("<b>Codice路 • Red Nacional de Ciudades Creativas</b><br/>"
                             "<font size=13 color='#1E3A8A'><b>GUÍA DE TRADUCCIÓN AL IDIOMA MISKITO</b></font><br/>"
                             f"<font size=8.5 color='#4B5563'>{subtitulo_modo}</font>", title_style)]],
            colWidths=[2.2 * inch, 5.3 * inch]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
    else:
        story.append(Paragraph("<b>Codice路 • GUÍA DE TRADUCCIÓN AL IDIOMA MISKITO</b>", title_style))
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
    t_resumen = Table(resumen_data, colWidths=[135, 135, 135, 135])
    t_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_resumen)
    story.append(Spacer(1, 10))

    # =========================================================================
    # RECUADRO DE CONTEXTO EXPLICATIVO PARA EL TRADUCTOR
    # =========================================================================
    contexto_html = (
        "<b>¿QUÉ ES CODICE路 Y PARA QUÉ SIRVE ESTE DOCUMENTO?</b><br/>"
        "Codice路 es la plataforma turística y cultural que conecta a los visitantes con la riqueza patrimonial, "
        "artística, artesanal y creativa de los municipios de Nicaragua. Nuestro objetivo con esta traducción es "
        "garantizar que la población hablante del <b>idioma Miskito (Miskitu)</b> y los visitantes de la Costa Caribe "
        "puedan disfrutar plenamente de la información turística en su propia lengua originaria.<br/><br/>"
        "<b>ESTRUCTURA Y SIGNIFICADO DE CADA ELEMENTO:</b><br/>"
        "• <b>Ciudad (Municipio):</b> Es el territorio principal. Su descripción presenta la identidad global, su historia "
        "y vocación cultural (ciudades creativas). <i>Se han excluido del documento las ciudades que no cuentan con circuitos creativos.</i><br/>"
        "• <b>Circuito Creativo (Ruta Temática):</b> Recorrido turístico planificado (a pie o vehicular) que agrupa "
        "atractivos culturales, murales, gastronomía o tradiciones dentro de la ciudad.<br/>"
        "• <b>Punto de Interés (Parada o Hito):</b> Cada una de las estaciones que componen el circuito (taller artesanal, "
        "monumento, museo, mirador o gastronomía típica). Se indica el orden y la categoría.<br/>"
        "• <b>Dato Histórico / Tradición:</b> Relatos, mitos, leyendas o saberes populares asociados a cada sitio.<br/>"
        "• <b>Evento / Festividad Cultural:</b> Fiestas patronales, festivales tradicionales, celebraciones religiosas y culturales "
        "(ej. La Gritería, Alfombras Pasionarias, festivales del tabaco o patronales). Incluye nombre, fechas y contexto.<br/><br/>"
        "<b>GUÍA PARA EL TRADUCTOR:</b><br/>"
        "1. <b>Filtro de Contenidos:</b> Este documento solo muestra los textos que <b>aún no han sido traducidos</b> al Miskito.<br/>"
        "2. Traduzca el texto en español respetando el sentido cultural. Los nombres propios (ej. 'Sutiaba', 'Monimbó') "
        "se pueden conservar o adaptar según la fonética del Miskito.<br/>"
        "3. Escriba en el espacio <b>'Traducción al Miskito / Miskitu bil'</b>.<br/>"
        "4. Cada elemento incluye un código único <b>[REF: ...]</b> indispensable para registrar la traducción en la base de datos sin equivocación."
    )

    t_contexto = Table([[Paragraph(contexto_html, context_body_style)]], colWidths=[540])
    t_contexto.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1.2, colors.HexColor("#3B82F6")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_contexto)
    story.append(Spacer(1, 10))

    # CASO ESPECIAL: Todo el contenido ya está traducido
    if len(ciudades_procesadas) == 0 and len(eventos_generales_items) == 0:
        completado_html = (
            "<font size=16 color='#047857'><b>🎉 ¡FELICIDADES! TRADUCCIÓN AL MISKITO COMPLETADA</b></font><br/><br/>"
            "<font size=11 color='#1F2937'>No se encontraron textos pendientes de traducción en las ciudades con circuitos creativos ni eventos.<br/>"
            "Todos los nombres, descripciones, festividades y puntos de interés ya cuentan con su equivalente en idioma Miskito (Miskitu bil).<br/><br/>"
            "Si deseas descargar la guía completa con todos los contenidos traducidos como respaldo o revisión, "
            "selecciona la opción <b>'Descargar Completo'</b> en el panel de control.</font>"
        )
        t_completado = Table([[Paragraph(completado_html, context_body_style)]], colWidths=[540])
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

    t_indice = Table(tabla_indice_data, colWidths=[95, 65, 65, 65, 250])
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
                Paragraph(f"<font size=13 color='white'><b>🏛️ CIUDAD: {ciudad.nombre.upper()}</b></font>", table_header_style),
                Paragraph(f"<font size=8.5 color='#E0E7FF'><b>{len(c_info['circuitos'])} Circuitos con pendientes</b> • ID Sistema #{ciudad.id}</font>", ParagraphStyle('R', parent=table_header_style, alignment=2))
            ]],
            colWidths=[330, 210]
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
                Paragraph(ciudad.nombre_miq if ciudad.nombre_miq else "<font color='#9CA3AF'>[ Escribir nombre en Miskito ]</font><br/><br/>________________________________________", col_miskito_style if ciudad.nombre_miq else col_write_prompt_style)
            ])

        if not solo_pendientes or c_info['descripcion_pendiente']:
            filas_ciudad.append([
                Paragraph(f"<b>Descripción Cultural</b><br/>"
                          f"<font size=7 color='#6B7280'>[REF: CIUDAD:{ciudad.id}:descripcion_miq]</font><br/>"
                          f"<font size=6.5 color='#92400E'>Resumen general cultural</font><br/>"
                          f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if c_info['descripcion_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                Paragraph(ciudad.descripcion or "<i>Sin descripción registrada</i>", col_spanish_style),
                Paragraph(ciudad.descripcion_miq if ciudad.descripcion_miq else "<font color='#9CA3AF'>[ Escribir traducción al Miskito de la descripción ]</font><br/><br/><br/><br/>________________________________________<br/>________________________________________", col_miskito_style if ciudad.descripcion_miq else col_write_prompt_style)
            ])

        # Datos Históricos generales de la ciudad
        for dh_dict in c_info['datos_historicos']:
            dh = dh_dict['objeto']
            filas_ciudad.append([
                Paragraph(f"<b>Dato Histórico / Leyenda</b><br/>"
                          f"<font size=7 color='#6B7280'>[REF: DATO:{dh.id}:titulo_miq & contenido_miq]</font><br/>"
                          f"<font size=6.5 color='#92400E'>Tipo: {dh.tipo}</font>", col_meta_style),
                Paragraph(f"<b>{dh.titulo}</b> ({dh.epoca_o_ano or 'Histórico'}):<br/>{dh.contenido}", col_spanish_style),
                Paragraph((dh.titulo_miq + "<br/>" + dh.contenido_miq) if (dh.titulo_miq and dh.contenido_miq) else "<font color='#9CA3AF'>[ Traducción de título e historia al Miskito ]</font><br/><br/><br/>________________________________________", col_miskito_style if dh.titulo_miq else col_write_prompt_style)
            ])

        if len(filas_ciudad) > 1:
            t_ciudad = Table(filas_ciudad, colWidths=[120, 210, 210])
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
                    Paragraph(f"<font size=10 color='white'><b>🎉 EVENTOS Y FESTIVIDADES CULTURALES ({len(eventos_ciudad)} pendiente(s))</b></font>", table_header_style),
                    Paragraph(f"<font size=8 color='#DDD6FE'>Festividades de {ciudad.nombre}</font>", ParagraphStyle('EVR', parent=table_header_style, alignment=2))
                ]],
                colWidths=[340, 200]
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
                        Paragraph(ev.titulo_miq if ev.titulo_miq else "<font color='#9CA3AF'>[ Escribir nombre del evento en Miskito ]</font><br/><br/>________________________________________", col_miskito_style if ev.titulo_miq else col_write_prompt_style)
                    ])

                if ev.rango_celebracion and (not solo_pendientes or ev_info['rango_pendiente']):
                    filas_evento.append([
                        Paragraph(f"<b>Fecha / Rango</b><br/>"
                                  f"<font size=7 color='#6B7280'>[REF: EVENTO:{ev.id}:rango_celebracion_miq]</font><br/>"
                                  f"<font size=6.5 color='#6D28D9'>Período tradicional de celebración</font><br/>"
                                  f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if ev_info['rango_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                        Paragraph(f"{ev.rango_celebracion}", col_spanish_style),
                        Paragraph(ev.rango_celebracion_miq if ev.rango_celebracion_miq else "<font color='#9CA3AF'>[ Escribir rango/fecha en Miskito ]</font><br/>________________________________________", col_miskito_style if ev.rango_celebracion_miq else col_write_prompt_style)
                    ])

                if not solo_pendientes or ev_info['descripcion_pendiente']:
                    filas_evento.append([
                        Paragraph(f"<b>Descripción del Evento</b><br/>"
                                  f"<font size=7 color='#6B7280'>[REF: EVENTO:{ev.id}:descripcion_miq]</font><br/>"
                                  f"<font size=6.5 color='#6D28D9'>Contexto de la festividad</font><br/>"
                                  f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if ev_info['descripcion_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                        Paragraph(ev.descripcion or "<i>Sin descripción</i>", col_spanish_style),
                        Paragraph(ev.descripcion_miq if ev.descripcion_miq else "<font color='#9CA3AF'>[ Escribir traducción al Miskito de la festividad ]</font><br/><br/><br/>________________________________________<br/>________________________________________", col_miskito_style if ev.descripcion_miq else col_write_prompt_style)
                    ])

                if len(filas_evento) > 1:
                    t_evento = Table(filas_evento, colWidths=[120, 210, 210])
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
                    story.append(KeepTogether(t_evento))
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
                    Paragraph(f"<font size=10 color='white'><b>🧭 CIRCUITO CREATIVO: {circuito.nombre.upper()}</b></font>", table_header_style),
                    Paragraph(f"<font size=8 color='#FEF3C7'>Dificultad: {circuito.dificultad} • {circuito.distancia_km} km • {circuito.duracion_estimada} • ID #{circuito.id}</font>", ParagraphStyle('CR', parent=table_header_style, alignment=2))
                ]],
                colWidths=[320, 220]
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
                    Paragraph(circuito.nombre_miq if circuito.nombre_miq else "<font color='#9CA3AF'>[ Escribir nombre del circuito en Miskito ]</font><br/><br/>________________________________________", col_miskito_style if circuito.nombre_miq else col_write_prompt_style)
                ])

            if not solo_pendientes or cir_info['descripcion_pendiente']:
                filas_circuito.append([
                    Paragraph(f"<b>Descripción del Recorrido</b><br/>"
                              f"<font size=7 color='#6B7280'>[REF: CIRCUITO:{circuito.id}:descripcion_miq]</font><br/>"
                              f"<font size=6.5 color='#92400E'>Contexto temático de la ruta</font><br/>"
                              f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if cir_info['descripcion_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                    Paragraph(circuito.descripcion or "<i>Sin descripción</i>", col_spanish_style),
                    Paragraph(circuito.descripcion_miq if circuito.descripcion_miq else "<font color='#9CA3AF'>[ Escribir descripción del circuito en Miskito ]</font><br/><br/><br/>________________________________________<br/>________________________________________", col_miskito_style if circuito.descripcion_miq else col_write_prompt_style)
                ])

            if len(filas_circuito) > 1:
                t_circuito = Table(filas_circuito, colWidths=[120, 210, 210])
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
                            Paragraph(p.nombre_miq if p.nombre_miq else "<font color='#9CA3AF'>[ Nombre del punto en Miskito ]</font><br/>________________________________________", col_miskito_style if p.nombre_miq else col_write_prompt_style)
                        ])

                    if not solo_pendientes or p_info['descripcion_pendiente']:
                        filas_punto.append([
                            Paragraph(f"<b>Descripción del Atractivo</b><br/>"
                                      f"<font size=7 color='#6B7280'>[REF: PUNTO:{p.id}:descripcion_miq]</font><br/>"
                                      f"<font size=6.5 color='#0F766E'>Explicación de qué se hace o aprecia aquí</font><br/>"
                                      f"{'<font size=6.5 color=\"#DC2626\">● Descripción pendiente</font>' if p_info['descripcion_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                            Paragraph(p.descripcion or "<i>Sin descripción</i>", col_spanish_style),
                            Paragraph(p.descripcion_miq if p.descripcion_miq else "<font color='#9CA3AF'>[ Traducción al Miskito del atractivo y actividades ]</font><br/><br/><br/>________________________________________<br/>________________________________________", col_miskito_style if p.descripcion_miq else col_write_prompt_style)
                        ])

                    # Datos históricos del punto
                    for dh_p_dict in p_info['datos_historicos']:
                        dh_p = dh_p_dict['objeto']
                        filas_punto.append([
                            Paragraph(f"<b>Dato / Tradición</b><br/>"
                                      f"<font size=7 color='#6B7280'>[REF: DATO:{dh_p.id}:titulo_miq & contenido_miq]<br/>Tipo: {dh_p.tipo}</font>", col_meta_style),
                            Paragraph(f"<b>{dh_p.titulo}</b>:<br/>{dh_p.contenido}", col_spanish_style),
                            Paragraph((dh_p.titulo_miq + "<br/>" + dh_p.contenido_miq) if (dh_p.titulo_miq and dh_p.contenido_miq) else "<font color='#9CA3AF'>[ Traducción de leyenda o tradición al Miskito ]</font><br/><br/>________________________________________", col_miskito_style if dh_p.titulo_miq else col_write_prompt_style)
                        ])

                    if len(filas_punto) > 0:
                        t_punto = Table(filas_punto, colWidths=[120, 210, 210])
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
                        story.append(KeepTogether(t_punto))
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
                Paragraph("<font size=13 color='white'><b>🎉 EVENTOS Y FESTIVIDADES NACIONALES / GENERALES</b></font>", table_header_style),
                Paragraph(f"<font size=8.5 color='#DDD6FE'><b>{len(eventos_generales_items)} Eventos con pendientes</b></font>", ParagraphStyle('EVGR', parent=table_header_style, alignment=2))
            ]],
            colWidths=[350, 190]
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
                    Paragraph(ev.titulo_miq if ev.titulo_miq else "<font color='#9CA3AF'>[ Escribir nombre del evento en Miskito ]</font><br/><br/>________________________________________", col_miskito_style if ev.titulo_miq else col_write_prompt_style)
                ])
            if ev.rango_celebracion and (not solo_pendientes or ev_g_info['rango_pendiente']):
                filas_ev_g.append([
                    Paragraph(f"<b>Fecha / Rango</b><br/>"
                              f"<font size=7 color='#6B7280'>[REF: EVENTO:{ev.id}:rango_celebracion_miq]</font><br/>"
                              f"<font size=6.5 color='#6D28D9'>Período tradicional de celebración</font><br/>"
                              f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if ev_g_info['rango_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                    Paragraph(f"{ev.rango_celebracion}", col_spanish_style),
                    Paragraph(ev.rango_celebracion_miq if ev.rango_celebracion_miq else "<font color='#9CA3AF'>[ Escribir rango/fecha en Miskito ]</font><br/>________________________________________", col_miskito_style if ev.rango_celebracion_miq else col_write_prompt_style)
                ])
            if not solo_pendientes or ev_g_info['descripcion_pendiente']:
                filas_ev_g.append([
                    Paragraph(f"<b>Descripción del Evento</b><br/>"
                              f"<font size=7 color='#6B7280'>[REF: EVENTO:{ev.id}:descripcion_miq]</font><br/>"
                              f"<font size=6.5 color='#6D28D9'>Contexto de la festividad</font><br/>"
                              f"{'<font size=6.5 color=\"#DC2626\">● Pendiente</font>' if ev_g_info['descripcion_pendiente'] else '<font size=6.5 color=\"#059669\">✓ Traducido</font>'}", col_meta_style),
                    Paragraph(ev.descripcion or "<i>Sin descripción</i>", col_spanish_style),
                    Paragraph(ev.descripcion_miq if ev.descripcion_miq else "<font color='#9CA3AF'>[ Escribir traducción al Miskito de la festividad ]</font><br/><br/><br/>________________________________________<br/>________________________________________", col_miskito_style if ev.descripcion_miq else col_write_prompt_style)
                ])

            if len(filas_ev_g) > 1:
                t_ev_g = Table(filas_ev_g, colWidths=[120, 210, 210])
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
                story.append(KeepTogether(t_ev_g))
                story.append(Spacer(1, 4))

    # Construir documento PDF con NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer_destino.seek(0)
    return buffer_destino
