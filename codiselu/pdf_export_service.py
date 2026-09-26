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

from .models import Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico


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


def generar_pdf_traduccion_miskito(ciudades_ids=None, buffer_destino=None) -> io.BytesIO:
    """
    Genera un documento PDF estructurado y visualmente claro para que traductores
    puedan traducir los contenidos de Ciudades, Circuitos Creativos y Puntos de Interés
    al idioma Miskito (Miskitu).

    Reglas de negocio aplicadas:
    - Excluye ciudades que no tengan circuitos creativos.
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
        'datos_historicos'
    ).order_by('nombre')

    ciudades = list(queryset)

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
    neutral_dark = colors.HexColor("#1F2937")      # Gris oscuro para lectura
    neutral_light = colors.HexColor("#F3F4F6")     # Fondo suave
    border_color = colors.HexColor("#D1D5DB")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=10
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=primary_color,
        spaceAfter=4
    )

    context_title_style = ParagraphStyle(
        'ContextTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=primary_color
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

    col_ref_style = ParagraphStyle(
        'ColRef',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#6B7280")
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
        textColor=colors.HexColor("#065F46")
    )

    col_write_prompt_style = ParagraphStyle(
        'ColWritePrompt',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#9CA3AF")
    )

    story = []

    # =========================================================================
    # PORTADA / ENCABEZADO Y GUÍA DE CONTEXTO PARA EL TRADUCTOR
    # =========================================================================

    # Fila de logotipo y título
    logo_path = os.path.join(settings.BASE_DIR, 'logocodicelu.png')
    header_data = []
    if os.path.exists(logo_path):
        img = Image(logo_path, width=2.0 * inch, height=0.9 * inch)
        header_table = Table(
            [[img, Paragraph("<b>Codice路 • Red Nacional de Ciudades Creativas</b><br/>"
                             "<font size=14 color='#1E3A8A'><b>GUÍA DE TRADUCCIÓN AL IDIOMA MISKITO</b></font><br/>"
                             "<font size=9 color='#6B7280'>Documento oficial de trabajo para traducción cultural (Miskitu bil)</font>", title_style)]],
            colWidths=[2.2 * inch, 5.3 * inch]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
    else:
        story.append(Paragraph("<b>Codice路 • GUÍA DE TRADUCCIÓN AL IDIOMA MISKITO</b>", title_style))
        story.append(Paragraph("Documentación oficial para traducción cultural al Miskitu", subtitle_style))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=8, spaceBefore=0))

    # Resumen y métricas
    total_circuitos = sum(c.circuitos.count() for c in ciudades)
    total_puntos = sum(sum(cir.puntos_interes.count() for cir in c.circuitos.all()) for c in ciudades)
    fecha_hoy = datetime.now().strftime("%d de %B de %Y")

    resumen_data = [
        [
            Paragraph(f"<b>Fecha de Emisión:</b> {fecha_hoy}", context_body_style),
            Paragraph(f"<b>Ciudades con Circuitos:</b> {len(ciudades)}", context_body_style),
            Paragraph(f"<b>Circuitos Creativos:</b> {total_circuitos}", context_body_style),
            Paragraph(f"<b>Puntos de Interés:</b> {total_puntos}", context_body_style),
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
        "y vocación cultural (ciudades creativas). <i>Nota: Se han excluido del documento las ciudades que aún no cuentan con circuitos creativos.</i><br/>"
        "• <b>Circuito Creativo (Ruta Temática):</b> Es un recorrido turístico planificado (a pie o en transporte) que agrupa "
        "atractivos culturales, murales, gastronomía o tradiciones representativas dentro de la ciudad.<br/>"
        "• <b>Punto de Interés (Parada o Hito):</b> Cada una de las estaciones que componen el circuito (un taller artesanal, "
        "un monumento colonial, un museo, un mirador natural o un restaurante típico). Se indica el orden y la categoría.<br/>"
        "• <b>Dato Histórico / Tradición:</b> Relatos, anécdotas, mitos, leyendas o saberes populares asociados a cada sitio.<br/><br/>"
        "<b>GUÍA PARA EL TRADUCTOR:</b><br/>"
        "1. Traduzca el texto en español respetando el sentido cultural y turístico. Si un nombre propio (ej. 'Monimbó', 'Sutiaba') "
        "no tiene traducción directa, manténgalo o adáptelo según la fonética del Miskito.<br/>"
        "2. Utilice el espacio <b>'Traducción al Miskito / Miskitu bil'</b> para redactar su propuesta.<br/>"
        "3. Cada elemento incluye un código <b>[REF: ...]</b> único. Este código es indispensable para que el equipo "
        "de desarrollo pueda incorporar la traducción directamente en la base de datos sin errores de asignación."
    )

    t_contexto = Table(
        [[Paragraph(contexto_html, context_body_style)]],
        colWidths=[540]
    )
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

    # Índice de Ciudades Incluidas
    story.append(Paragraph("<b>Índice de Ciudades Seleccionadas con Circuitos Creativos:</b>", section_header_style))
    tabla_indice_data = [
        [
            Paragraph("<b>Ciudad</b>", table_header_style),
            Paragraph("<b>Circuitos</b>", table_header_style),
            Paragraph("<b>Puntos Totales</b>", table_header_style),
            Paragraph("<b>Circuitos Incluidos</b>", table_header_style)
        ]
    ]
    for c in ciudades:
        circuitos_nombres = ", ".join([cir.nombre for cir in c.circuitos.all()])
        puntos_ciudad = sum(cir.puntos_interes.count() for cir in c.circuitos.all())
        tabla_indice_data.append([
            Paragraph(f"<b>{c.nombre}</b>", col_meta_style),
            Paragraph(f"{c.circuitos.count()} circuitos", col_spanish_style),
            Paragraph(f"{puntos_ciudad} paradas", col_spanish_style),
            Paragraph(f"<font size=7 color='#4B5563'>{circuitos_nombres}</font>", col_spanish_style),
        ])

    t_indice = Table(tabla_indice_data, colWidths=[100, 75, 75, 290])
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

    for idx_c, ciudad in enumerate(ciudades):
        if idx_c > 0:
            story.append(PageBreak())

        # Banner de Ciudad
        banner_ciudad = Table(
            [[
                Paragraph(f"<font size=13 color='white'><b>🏛️ CIUDAD: {ciudad.nombre.upper()}</b></font>", table_header_style),
                Paragraph(f"<font size=9 color='#E0E7FF'><b>{ciudad.circuitos.count()} Circuitos Creativos</b> • ID Sistema #{ciudad.id}</font>", ParagraphStyle('R', parent=table_header_style, alignment=2))
            ]],
            colWidths=[340, 200]
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

        # Tabla de Traducción de la Ciudad
        filas_ciudad = [
            [
                Paragraph("<b>Campo & Referencia</b>", table_header_style),
                Paragraph("<b>Texto Original en Español</b>", table_header_style),
                Paragraph("<b>Traducción al Miskito (Miskitu bil)</b>", table_header_style),
            ],
            # Nombre de la Ciudad
            [
                Paragraph(f"<b>Nombre Ciudad</b><br/>"
                          f"<font size=7 color='#6B7280'>[REF: CIUDAD:{ciudad.id}:nombre_miq]</font><br/>"
                          f"<font size=6.5 color='#92400E'>Título principal del municipio</font>", col_meta_style),
                Paragraph(f"<b>{ciudad.nombre}</b>", col_spanish_style),
                Paragraph(ciudad.nombre_miq if ciudad.nombre_miq else "<font color='#9CA3AF'>[ Escribir nombre en Miskito ]</font><br/><br/>________________________________________", col_miskito_style if ciudad.nombre_miq else col_write_prompt_style)
            ],
            # Descripción de la Ciudad
            [
                Paragraph(f"<b>Descripción Cultural</b><br/>"
                          f"<font size=7 color='#6B7280'>[REF: CIUDAD:{ciudad.id}:descripcion_miq]</font><br/>"
                          f"<font size=6.5 color='#92400E'>Resumen general de historia y vocación creativa</font>", col_meta_style),
                Paragraph(ciudad.descripcion or "<i>Sin descripción registrada</i>", col_spanish_style),
                Paragraph(ciudad.descripcion_miq if ciudad.descripcion_miq else "<font color='#9CA3AF'>[ Escribir traducción al Miskito de la descripción cultural ]</font><br/><br/><br/><br/>________________________________________<br/>________________________________________", col_miskito_style if ciudad.descripcion_miq else col_write_prompt_style)
            ]
        ]

        # Si la ciudad tiene Datos Históricos generales
        for dh in ciudad.datos_historicos.filter(punto_interes__isnull=True):
            filas_ciudad.append([
                Paragraph(f"<b>Dato Histórico / Leyenda</b><br/>"
                          f"<font size=7 color='#6B7280'>[REF: DATO:{dh.id}:titulo_miq & contenido_miq]</font><br/>"
                          f"<font size=6.5 color='#92400E'>Tipo: {dh.tipo}</font>", col_meta_style),
                Paragraph(f"<b>{dh.titulo}</b> ({dh.epoca_o_ano or 'Histórico'}):<br/>{dh.contenido}", col_spanish_style),
                Paragraph((dh.titulo_miq + "<br/>" + dh.contenido_miq) if (dh.titulo_miq and dh.contenido_miq) else "<font color='#9CA3AF'>[ Traducción de título e historia al Miskito ]</font><br/><br/><br/>________________________________________", col_miskito_style if dh.titulo_miq else col_write_prompt_style)
            ])

        t_ciudad = Table(filas_ciudad, colWidths=[120, 210, 210])
        t_ciudad.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
            ('BOX', (0, 0), (-1, -1), 1, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#F8FAFC")),
            ('BACKGROUND', (2, 1), (2, -1), colors.HexColor("#FEFCE8")),  # Fondo ligeramente cálido para traducción
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t_ciudad)
        story.append(Spacer(1, 10))

        # =====================================================================
        # CIRCUITOS CREATIVOS DENTRO DE LA CIUDAD
        # =====================================================================
        for idx_cir, circuito in enumerate(ciudad.circuitos.all()):
            story.append(Spacer(1, 4))
            
            # Sub-banner Circuito
            banner_circuito = Table(
                [[
                    Paragraph(f"<font size=10 color='white'><b>🧭 CIRCUITO CREATIVO #{idx_cir + 1}: {circuito.nombre.upper()}</b></font>", table_header_style),
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
                ],
                # Nombre del Circuito
                [
                    Paragraph(f"<b>Nombre del Circuito</b><br/>"
                              f"<font size=7 color='#6B7280'>[REF: CIRCUITO:{circuito.id}:nombre_miq]</font><br/>"
                              f"<font size=6.5 color='#92400E'>Nombre oficial del recorrido</font>", col_meta_style),
                    Paragraph(f"<b>{circuito.nombre}</b>", col_spanish_style),
                    Paragraph(circuito.nombre_miq if circuito.nombre_miq else "<font color='#9CA3AF'>[ Escribir nombre del circuito en Miskito ]</font><br/><br/>________________________________________", col_miskito_style if circuito.nombre_miq else col_write_prompt_style)
                ],
                # Descripción del Circuito
                [
                    Paragraph(f"<b>Descripción del Recorrido</b><br/>"
                              f"<font size=7 color='#6B7280'>[REF: CIRCUITO:{circuito.id}:descripcion_miq]</font><br/>"
                              f"<font size=6.5 color='#92400E'>Contexto temático de la ruta</font>", col_meta_style),
                    Paragraph(circuito.descripcion or "<i>Sin descripción</i>", col_spanish_style),
                    Paragraph(circuito.descripcion_miq if circuito.descripcion_miq else "<font color='#9CA3AF'>[ Escribir descripción del circuito en Miskito ]</font><br/><br/><br/>________________________________________<br/>________________________________________", col_miskito_style if circuito.descripcion_miq else col_write_prompt_style)
                ]
            ]

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
            story.append(Spacer(1, 6))

            # -----------------------------------------------------------------
            # PUNTOS DE INTERÉS DEL CIRCUITO
            # -----------------------------------------------------------------
            puntos = circuito.puntos_interes.all()
            if puntos.exists():
                story.append(Paragraph(f"<b>Paradas y Puntos de Interés de la Ruta ({puntos.count()} estaciones):</b>", section_header_style))

                for p in puntos:
                    filas_punto = [
                        [
                            Paragraph(f"<b>Parada #{p.orden}: {p.nombre}</b><br/>"
                                      f"<font size=7 color='#6B7280'>Categoría: {p.get_tipo_display()}<br/>[REF: PUNTO:{p.id}:nombre_miq]</font>", col_meta_style),
                            Paragraph(f"<b>{p.nombre}</b>", col_spanish_style),
                            Paragraph(p.nombre_miq if p.nombre_miq else "<font color='#9CA3AF'>[ Nombre del punto en Miskito ]</font><br/>________________________________________", col_miskito_style if p.nombre_miq else col_write_prompt_style)
                        ],
                        [
                            Paragraph(f"<b>Descripción del Atractivo</b><br/>"
                                      f"<font size=7 color='#6B7280'>[REF: PUNTO:{p.id}:descripcion_miq]</font><br/>"
                                      f"<font size=6.5 color='#0F766E'>Explicación de qué se hace o aprecia aquí</font>", col_meta_style),
                            Paragraph(p.descripcion or "<i>Sin descripción</i>", col_spanish_style),
                            Paragraph(p.descripcion_miq if p.descripcion_miq else "<font color='#9CA3AF'>[ Traducción al Miskito del atractivo y actividades ]</font><br/><br/><br/>________________________________________<br/>________________________________________", col_miskito_style if p.descripcion_miq else col_write_prompt_style)
                        ]
                    ]

                    # Si el punto tiene Datos Históricos o Tradiciones asociadas
                    for dh_p in p.datos_historicos.all():
                        filas_punto.append([
                            Paragraph(f"<b>Dato / Tradición</b><br/>"
                                      f"<font size=7 color='#6B7280'>[REF: DATO:{dh_p.id}:titulo_miq & contenido_miq]<br/>Tipo: {dh_p.tipo}</font>", col_meta_style),
                            Paragraph(f"<b>{dh_p.titulo}</b>:<br/>{dh_p.contenido}", col_spanish_style),
                            Paragraph((dh_p.titulo_miq + "<br/>" + dh_p.contenido_miq) if (dh_p.titulo_miq and dh_p.contenido_miq) else "<font color='#9CA3AF'>[ Traducción de leyenda o tradición al Miskito ]</font><br/><br/>________________________________________", col_miskito_style if dh_p.titulo_miq else col_write_prompt_style)
                        ])

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
                    # Mantener cada punto de interés agrupado para evitar cortes feos si es posible
                    story.append(KeepTogether(t_punto))
                    story.append(Spacer(1, 4))

            story.append(Spacer(1, 8))

    # Construir documento PDF con NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer_destino.seek(0)
    return buffer_destino
