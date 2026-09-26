import io
from datetime import datetime
from django.db.models import Prefetch

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from .models import Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico, Evento


def tiene_traduccion(valor) -> bool:
    """Verifica si un campo ya posee traducción al Miskito (no nulo y no en blanco)."""
    return bool(valor and str(valor).strip())


def generar_excel_traduccion_miskito(ciudades_ids=None, solo_pendientes: bool = True) -> io.BytesIO:
    """
    Genera un libro de Excel (.xlsx) estructurado, visualmente enriquecido y optimizado
    para que los traductores comunitarios trabajen cómodamente en la traducción de
    los contenidos oficiales de Ciudades, Circuitos, Paradas, Leyendas y Eventos
    al idioma Miskito (Miskitu bil).

    Reglas aplicadas:
    - Incluye solo ciudades con circuitos creativos activos.
    - Si solo_pendientes=True: incluye únicamente los campos que no tienen traducción al Miskito.
    - Hoja 1: 'Instrucciones y Resumen' con contexto cultural, métricas e instrucciones.
    - Hoja 2: 'Plantilla de Traducción' con tabla de datos, filtros automáticos (AutoFilter),
      cabecera congelada (Freeze Panes), anchos automáticos y columna de traducción destacada.
    - Cada fila cuenta con su código técnico [REF] para sincronización unívoca con la BD.
    """
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

    # Recolección de filas y conteo de métricas
    filas_traduccion = []
    conteo_campos_pendientes = 0
    conteo_campos_traducidos = 0
    ciudades_con_pendientes = set()
    circuitos_con_pendientes = set()
    puntos_con_pendientes = set()
    eventos_con_pendientes = set()

    for ciudad in ciudades:
        # 1. Nombre de la ciudad
        c_nom_pend = not tiene_traduccion(ciudad.nombre_miq)
        if c_nom_pend: conteo_campos_pendientes += 1
        else: conteo_campos_traducidos += 1

        if not solo_pendientes or c_nom_pend:
            ciudades_con_pendientes.add(ciudad.id)
            filas_traduccion.append({
                'ref': f"CIUDAD:{ciudad.id}:nombre_miq",
                'ambito': "Ciudad",
                'ciudad': ciudad.nombre,
                'circuito': "—",
                'elemento': f"Municipio de {ciudad.nombre}",
                'campo': "Nombre de Ciudad",
                'texto_es': ciudad.nombre,
                'texto_miq': ciudad.nombre_miq or "",
                'es_pendiente': c_nom_pend,
                'guia': "[ Escribir nombre en Miskito ]"
            })

        # 2. Descripción de la ciudad
        c_desc_pend = not tiene_traduccion(ciudad.descripcion_miq)
        if c_desc_pend: conteo_campos_pendientes += 1
        else: conteo_campos_traducidos += 1

        if not solo_pendientes or c_desc_pend:
            ciudades_con_pendientes.add(ciudad.id)
            filas_traduccion.append({
                'ref': f"CIUDAD:{ciudad.id}:descripcion_miq",
                'ambito': "Ciudad",
                'ciudad': ciudad.nombre,
                'circuito': "—",
                'elemento': f"Municipio de {ciudad.nombre}",
                'campo': "Descripción Cultural",
                'texto_es': ciudad.descripcion,
                'texto_miq': ciudad.descripcion_miq or "",
                'es_pendiente': c_desc_pend,
                'guia': "[ Escribir descripción cultural en Miskito ]"
            })

        # 3. Datos Históricos a nivel de Ciudad
        for dh in ciudad.datos_historicos.filter(punto_interes__isnull=True):
            dh_tit_pend = not tiene_traduccion(dh.titulo_miq)
            dh_cont_pend = not tiene_traduccion(dh.contenido_miq)

            if dh_tit_pend: conteo_campos_pendientes += 1
            else: conteo_campos_traducidos += 1
            if dh_cont_pend: conteo_campos_pendientes += 1
            else: conteo_campos_traducidos += 1

            if not solo_pendientes or dh_tit_pend:
                ciudades_con_pendientes.add(ciudad.id)
                filas_traduccion.append({
                    'ref': f"DATO:{dh.id}:titulo_miq",
                    'ambito': "Dato Histórico",
                    'ciudad': ciudad.nombre,
                    'circuito': "—",
                    'elemento': f"Historia / Leyenda ({dh.epoca_o_ano or 'Histórico'})",
                    'campo': "Título de la Historia",
                    'texto_es': dh.titulo,
                    'texto_miq': dh.titulo_miq or "",
                    'es_pendiente': dh_tit_pend,
                    'guia': "[ Escribir título del relato en Miskito ]"
                })

            if not solo_pendientes or dh_cont_pend:
                ciudades_con_pendientes.add(ciudad.id)
                filas_traduccion.append({
                    'ref': f"DATO:{dh.id}:contenido_miq",
                    'ambito': "Dato Histórico",
                    'ciudad': ciudad.nombre,
                    'circuito': "—",
                    'elemento': f"Historia / Leyenda: {dh.titulo}",
                    'campo': "Contenido / Leyenda",
                    'texto_es': dh.contenido,
                    'texto_miq': dh.contenido_miq or "",
                    'es_pendiente': dh_cont_pend,
                    'guia': "[ Escribir narración completa en Miskito ]"
                })

        # 4. Eventos Culturales de la Ciudad
        for ev in ciudad.eventos.all():
            ev_tit_pend = not tiene_traduccion(ev.titulo_miq)
            ev_rango_pend = bool(ev.rango_celebracion and not tiene_traduccion(ev.rango_celebracion_miq))
            ev_desc_pend = not tiene_traduccion(ev.descripcion_miq)

            if ev_tit_pend: conteo_campos_pendientes += 1
            else: conteo_campos_traducidos += 1

            if ev.rango_celebracion:
                if ev_rango_pend: conteo_campos_pendientes += 1
                else: conteo_campos_traducidos += 1

            if ev_desc_pend: conteo_campos_pendientes += 1
            else: conteo_campos_traducidos += 1

            if not solo_pendientes or ev_tit_pend:
                ciudades_con_pendientes.add(ciudad.id)
                eventos_con_pendientes.add(ev.id)
                filas_traduccion.append({
                    'ref': f"EVENTO:{ev.id}:titulo_miq",
                    'ambito': "Evento Cultural",
                    'ciudad': ciudad.nombre,
                    'circuito': "—",
                    'elemento': f"Festividad: {ev.titulo}",
                    'campo': "Nombre del Evento",
                    'texto_es': ev.titulo,
                    'texto_miq': ev.titulo_miq or "",
                    'es_pendiente': ev_tit_pend,
                    'guia': "[ Escribir nombre del evento/fiesta en Miskito ]"
                })

            if ev.rango_celebracion and (not solo_pendientes or ev_rango_pend):
                ciudades_con_pendientes.add(ciudad.id)
                eventos_con_pendientes.add(ev.id)
                filas_traduccion.append({
                    'ref': f"EVENTO:{ev.id}:rango_celebracion_miq",
                    'ambito': "Evento Cultural",
                    'ciudad': ciudad.nombre,
                    'circuito': "—",
                    'elemento': f"Festividad: {ev.titulo}",
                    'campo': "Fecha / Rango de Celebración",
                    'texto_es': ev.rango_celebracion,
                    'texto_miq': ev.rango_celebracion_miq or "",
                    'es_pendiente': ev_rango_pend,
                    'guia': "[ Escribir fecha o época de celebración en Miskito ]"
                })

            if not solo_pendientes or ev_desc_pend:
                ciudades_con_pendientes.add(ciudad.id)
                eventos_con_pendientes.add(ev.id)
                filas_traduccion.append({
                    'ref': f"EVENTO:{ev.id}:descripcion_miq",
                    'ambito': "Evento Cultural",
                    'ciudad': ciudad.nombre,
                    'circuito': "—",
                    'elemento': f"Festividad: {ev.titulo}",
                    'campo': "Descripción del Evento",
                    'texto_es': ev.descripcion,
                    'texto_miq': ev.descripcion_miq or "",
                    'es_pendiente': ev_desc_pend,
                    'guia': "[ Escribir descripción cultural del evento en Miskito ]"
                })

        # 5. Circuitos Creativos y Puntos de Interés
        for cir in ciudad.circuitos.all():
            cir_nom_pend = not tiene_traduccion(cir.nombre_miq)
            cir_desc_pend = not tiene_traduccion(cir.descripcion_miq)

            if cir_nom_pend: conteo_campos_pendientes += 1
            else: conteo_campos_traducidos += 1
            if cir_desc_pend: conteo_campos_pendientes += 1
            else: conteo_campos_traducidos += 1

            if not solo_pendientes or cir_nom_pend:
                ciudades_con_pendientes.add(ciudad.id)
                circuitos_con_pendientes.add(cir.id)
                filas_traduccion.append({
                    'ref': f"CIRCUITO:{cir.id}:nombre_miq",
                    'ambito': "Circuito Creativo",
                    'ciudad': ciudad.nombre,
                    'circuito': cir.nombre,
                    'elemento': f"Ruta: {cir.nombre}",
                    'campo': "Nombre del Circuito",
                    'texto_es': cir.nombre,
                    'texto_miq': cir.nombre_miq or "",
                    'es_pendiente': cir_nom_pend,
                    'guia': "[ Escribir nombre del circuito en Miskito ]"
                })

            if not solo_pendientes or cir_desc_pend:
                ciudades_con_pendientes.add(ciudad.id)
                circuitos_con_pendientes.add(cir.id)
                filas_traduccion.append({
                    'ref': f"CIRCUITO:{cir.id}:descripcion_miq",
                    'ambito': "Circuito Creativo",
                    'ciudad': ciudad.nombre,
                    'circuito': cir.nombre,
                    'elemento': f"Ruta: {cir.nombre}",
                    'campo': "Descripción del Recorrido",
                    'texto_es': cir.descripcion,
                    'texto_miq': cir.descripcion_miq or "",
                    'es_pendiente': cir_desc_pend,
                    'guia': "[ Escribir descripción de la ruta en Miskito ]"
                })

            # Puntos de interés del circuito
            for p in cir.puntos_interes.all():
                p_nom_pend = not tiene_traduccion(p.nombre_miq)
                p_desc_pend = not tiene_traduccion(p.descripcion_miq)

                if p_nom_pend: conteo_campos_pendientes += 1
                else: conteo_campos_traducidos += 1
                if p_desc_pend: conteo_campos_pendientes += 1
                else: conteo_campos_traducidos += 1

                if not solo_pendientes or p_nom_pend:
                    ciudades_con_pendientes.add(ciudad.id)
                    circuitos_con_pendientes.add(cir.id)
                    puntos_con_pendientes.add(p.id)
                    filas_traduccion.append({
                        'ref': f"PUNTO:{p.id}:nombre_miq",
                        'ambito': "Punto de Interés",
                        'ciudad': ciudad.nombre,
                        'circuito': cir.nombre,
                        'elemento': f"Parada #{p.orden}: {p.nombre}",
                        'campo': "Nombre de la Parada",
                        'texto_es': p.nombre,
                        'texto_miq': p.nombre_miq or "",
                        'es_pendiente': p_nom_pend,
                        'guia': f"[ Escribir nombre en Miskito • Tipo: {p.get_tipo_display()} ]"
                    })

                if not solo_pendientes or p_desc_pend:
                    ciudades_con_pendientes.add(ciudad.id)
                    circuitos_con_pendientes.add(cir.id)
                    puntos_con_pendientes.add(p.id)
                    filas_traduccion.append({
                        'ref': f"PUNTO:{p.id}:descripcion_miq",
                        'ambito': "Punto de Interés",
                        'ciudad': ciudad.nombre,
                        'circuito': cir.nombre,
                        'elemento': f"Parada #{p.orden}: {p.nombre}",
                        'campo': "Descripción del Atractivo",
                        'texto_es': p.descripcion,
                        'texto_miq': p.descripcion_miq or "",
                        'es_pendiente': p_desc_pend,
                        'guia': "[ Escribir descripción del atractivo en Miskito ]"
                    })

                # Datos Históricos del punto de interés
                for dh_p in p.datos_historicos.all():
                    dhp_tit_pend = not tiene_traduccion(dh_p.titulo_miq)
                    dhp_cont_pend = not tiene_traduccion(dh_p.contenido_miq)

                    if dhp_tit_pend: conteo_campos_pendientes += 1
                    else: conteo_campos_traducidos += 1
                    if dhp_cont_pend: conteo_campos_pendientes += 1
                    else: conteo_campos_traducidos += 1

                    if not solo_pendientes or dhp_tit_pend:
                        ciudades_con_pendientes.add(ciudad.id)
                        circuitos_con_pendientes.add(cir.id)
                        puntos_con_pendientes.add(p.id)
                        filas_traduccion.append({
                            'ref': f"DATO:{dh_p.id}:titulo_miq",
                            'ambito': "Dato Histórico",
                            'ciudad': ciudad.nombre,
                            'circuito': cir.nombre,
                            'elemento': f"Parada #{p.orden} ({p.nombre})",
                            'campo': f"Título Historia ({dh_p.tipo})",
                            'texto_es': dh_p.titulo,
                            'texto_miq': dh_p.titulo_miq or "",
                            'es_pendiente': dhp_tit_pend,
                            'guia': "[ Escribir título del dato histórico en Miskito ]"
                        })

                    if not solo_pendientes or dhp_cont_pend:
                        ciudades_con_pendientes.add(ciudad.id)
                        circuitos_con_pendientes.add(cir.id)
                        puntos_con_pendientes.add(p.id)
                        filas_traduccion.append({
                            'ref': f"DATO:{dh_p.id}:contenido_miq",
                            'ambito': "Dato Histórico",
                            'ciudad': ciudad.nombre,
                            'circuito': cir.nombre,
                            'elemento': f"Parada #{p.orden} ({p.nombre}) - {dh_p.titulo}",
                            'campo': "Contenido de la Historia",
                            'texto_es': dh_p.contenido,
                            'texto_miq': dh_p.contenido_miq or "",
                            'es_pendiente': dhp_cont_pend,
                            'guia': "[ Escribir narración histórica en Miskito ]"
                        })

    # 6. Eventos Culturales Generales / Nacionales (sin ciudad asociada)
    eventos_generales = Evento.objects.filter(ciudad__isnull=True, esta_activo=True).order_by('fecha_inicio')
    for ev_g in eventos_generales:
        evg_tit_pend = not tiene_traduccion(ev_g.titulo_miq)
        evg_rango_pend = bool(ev_g.rango_celebracion and not tiene_traduccion(ev_g.rango_celebracion_miq))
        evg_desc_pend = not tiene_traduccion(ev_g.descripcion_miq)

        if evg_tit_pend: conteo_campos_pendientes += 1
        else: conteo_campos_traducidos += 1
        if ev_g.rango_celebracion:
            if evg_rango_pend: conteo_campos_pendientes += 1
            else: conteo_campos_traducidos += 1
        if evg_desc_pend: conteo_campos_pendientes += 1
        else: conteo_campos_traducidos += 1

        if not solo_pendientes or evg_tit_pend:
            eventos_con_pendientes.add(ev_g.id)
            filas_traduccion.append({
                'ref': f"EVENTO:{ev_g.id}:titulo_miq",
                'ambito': "Evento Cultural",
                'ciudad': "Nacional / General",
                'circuito': "—",
                'elemento': f"Festividad: {ev_g.titulo}",
                'campo': "Nombre del Evento",
                'texto_es': ev_g.titulo,
                'texto_miq': ev_g.titulo_miq or "",
                'es_pendiente': evg_tit_pend,
                'guia': "[ Escribir nombre del evento en Miskito ]"
            })

        if ev_g.rango_celebracion and (not solo_pendientes or evg_rango_pend):
            eventos_con_pendientes.add(ev_g.id)
            filas_traduccion.append({
                'ref': f"EVENTO:{ev_g.id}:rango_celebracion_miq",
                'ambito': "Evento Cultural",
                'ciudad': "Nacional / General",
                'circuito': "—",
                'elemento': f"Festividad: {ev_g.titulo}",
                'campo': "Fecha / Rango de Celebración",
                'texto_es': ev_g.rango_celebracion,
                'texto_miq': ev_g.rango_celebracion_miq or "",
                'es_pendiente': evg_rango_pend,
                'guia': "[ Escribir fecha o época de celebración en Miskito ]"
            })

        if not solo_pendientes or evg_desc_pend:
            eventos_con_pendientes.add(ev_g.id)
            filas_traduccion.append({
                'ref': f"EVENTO:{ev_g.id}:descripcion_miq",
                'ambito': "Evento Cultural",
                'ciudad': "Nacional / General",
                'circuito': "—",
                'elemento': f"Festividad: {ev_g.titulo}",
                'campo': "Descripción del Evento",
                'texto_es': ev_g.descripcion,
                'texto_miq': ev_g.descripcion_miq or "",
                'es_pendiente': evg_desc_pend,
                'guia': "[ Escribir descripción cultural del evento en Miskito ]"
            })

    # =========================================================================
    # CREACIÓN DEL WORKBOOK OPENPYXL CON ESTILOS VISUALES PREMIUM
    # =========================================================================
    wb = openpyxl.Workbook()

    # Paleta de Colores Corporativos Codice Lu
    # Primario Codice: Azul Marino Profundo #1E3A8A
    # Acento Excel / Miskito: Verde Esmeralda #107C41 / #059669
    # Alerta / Pendiente: Rojo Carmesí #DC2626 / Suave #FEF2F2
    # Exito / Traducido: Verde #16A34A / Suave #ECFDF5
    # Fondo Editable Traductor: Verde menta claro #F0FDF4
    # Bordes: Gris claro #D1D5DB
    borde_fino = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )
    borde_encabezado = Border(
        left=Side(style='thin', color='94A3B8'),
        right=Side(style='thin', color='94A3B8'),
        top=Side(style='medium', color='1E3A8A'),
        bottom=Side(style='medium', color='1E3A8A')
    )

    # -------------------------------------------------------------------------
    # HOJA 1: INSTRUCCIONES Y RESUMEN
    # -------------------------------------------------------------------------
    ws_info = wb.active
    ws_info.title = "Instrucciones y Resumen"
    ws_info.sheet_properties.tabColor = "1E3A8A"
    ws_info.views.sheetView[0].showGridLines = True

    # Banner de Título
    ws_info.merge_cells('A1:G1')
    c_banner1 = ws_info['A1']
    c_banner1.value = "Codice Lu • Red Nacional de Ciudades Creativas de Nicaragua"
    c_banner1.font = Font(name='Calibri', size=15, bold=True, color='FFFFFF')
    c_banner1.fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    c_banner1.alignment = Alignment(horizontal='center', vertical='center')
    ws_info.row_dimensions[1].height = 36

    ws_info.merge_cells('A2:G2')
    c_banner2 = ws_info['A2']
    c_banner2.value = "PLANTILLA OFICIAL DE TRADUCCIÓN AL IDIOMA MISKITO (MISKITU BIL)"
    c_banner2.font = Font(name='Calibri', size=13, bold=True, color='FFFFFF')
    c_banner2.fill = PatternFill(start_color='1E40AF', end_color='1E40AF', fill_type='solid')
    c_banner2.alignment = Alignment(horizontal='center', vertical='center')
    ws_info.row_dimensions[2].height = 28

    ws_info.merge_cells('A3:G3')
    c_banner3 = ws_info['A3']
    subtitulo_filtro = "Filtro activo: Únicamente textos pendientes por traducir" if solo_pendientes else "Modo: Documentación Completa"
    c_banner3.value = f"Uso confidencial para el equipo de traducción comunitaria • {subtitulo_filtro}"
    c_banner3.font = Font(name='Calibri', size=10, italic=True, color='FFFFFF')
    c_banner3.fill = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
    c_banner3.alignment = Alignment(horizontal='center', vertical='center')
    ws_info.row_dimensions[3].height = 22

    # Tabla Resumen / Métricas de Traducción
    ws_info.cell(row=5, column=1, value="MÉTRICAS DEL DOCUMENTO").font = Font(name='Calibri', size=11, bold=True, color='1E3A8A')
    
    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    kpis = [
        ("Fecha de Generación:", fecha_hoy, "Filtro Seleccionado:", "Solo Pendientes" if solo_pendientes else "Completo"),
        ("Ciudades con Pendientes:", len(ciudades_con_pendientes), "Circuitos Creativos:", len(circuitos_con_pendientes)),
        ("Paradas / Hitos Culturales:", len(puntos_con_pendientes), "Eventos Culturales:", len(eventos_con_pendientes)),
        ("Campos Por Traducir:", conteo_campos_pendientes, "Campos Ya Traducidos:", conteo_campos_traducidos),
    ]

    for i, (k1, v1, k2, v2) in enumerate(kpis, start=6):
        ws_info.row_dimensions[i].height = 22
        # Col 1 y 2
        c1 = ws_info.cell(row=i, column=1, value=k1)
        c1.font = Font(name='Calibri', size=10, bold=True, color='374151')
        c1.fill = PatternFill(start_color='F3F4F6', end_color='F3F4F6', fill_type='solid')
        c1.border = borde_fino

        c2 = ws_info.cell(row=i, column=2, value=v1)
        c2.font = Font(name='Calibri', size=10, bold=(k1 == "Campos Por Traducir:"), color='DC2626' if k1 == "Campos Por Traducir:" else '111827')
        c2.alignment = Alignment(horizontal='center')
        c2.fill = PatternFill(start_color='FEF2F2' if k1 == "Campos Por Traducir:" else 'FFFFFF', end_color='FEF2F2' if k1 == "Campos Por Traducir:" else 'FFFFFF', fill_type='solid')
        c2.border = borde_fino

        # Col 3 vacía como separador
        # Col 4 y 5
        c4 = ws_info.cell(row=i, column=4, value=k2)
        c4.font = Font(name='Calibri', size=10, bold=True, color='374151')
        c4.fill = PatternFill(start_color='F3F4F6', end_color='F3F4F6', fill_type='solid')
        c4.border = borde_fino

        c5 = ws_info.cell(row=i, column=5, value=v2)
        c5.font = Font(name='Calibri', size=10, bold=(k2 == "Campos Ya Traducidos:"), color='059669' if k2 == "Campos Ya Traducidos:" else '111827')
        c5.alignment = Alignment(horizontal='center')
        c5.fill = PatternFill(start_color='ECFDF5' if k2 == "Campos Ya Traducidos:" else 'FFFFFF', end_color='ECFDF5' if k2 == "Campos Ya Traducidos:" else 'FFFFFF', fill_type='solid')
        c5.border = borde_fino

    # Instrucciones Clave
    ws_info.cell(row=11, column=1, value="INSTRUCCIONES CLAVE PARA EL EQUIPO TRADUCTOR").font = Font(name='Calibri', size=11, bold=True, color='1E3A8A')
    
    instrucciones = [
        "1. Pestaña de Trabajo: Diríjase a la pestaña 'Plantilla de Traducción' ubicada en la parte inferior de este archivo.",
        "2. Dónde Escribir: Escriba su traducción directamente en la columna H resaltada en color verde ('Traducción al Miskito (Miskitu bil)').",
        "3. Código Técnico [REF]: NO modifique ni elimine los códigos de la columna A (ej. 'CIUDAD:1:nombre_miq'). Estos identificadores permiten que el sistema cargue automáticamente sus traducciones a la base de datos sin errores ni confusiones.",
        "4. Filtros Automáticos: Puede utilizar las flechas de filtro en los encabezados para trabajar por Ciudad específica, por Circuito o por tipo de elemento.",
        "5. Fidelidad Cultural: Respete el sentido cultural y tradicional de cada historia, leyenda o festividad. Los nombres propios (ej. 'Monimbó', 'Sutiaba') se pueden conservar o adaptar conforme a la fonética habitual del Miskitu bil.",
        "6. Guardado: Al finalizar, guarde este archivo en formato .xlsx y remítalo al equipo de administración para su importación centralizada."
    ]

    for idx, inst in enumerate(instrucciones, start=12):
        ws_info.row_dimensions[idx].height = 20
        ws_info.merge_cells(start_row=idx, start_column=1, end_row=idx, end_column=7)
        c_inst = ws_info.cell(row=idx, column=1, value=inst)
        c_inst.font = Font(name='Calibri', size=9.5, color='1F2937')
        c_inst.alignment = Alignment(vertical='center')

    # Ficha de Registro del Traductor
    ws_info.cell(row=19, column=1, value="FICHA DE CONTROL DEL TRADUCTOR(A)").font = Font(name='Calibri', size=11, bold=True, color='1E3A8A')
    
    ficha_items = [
        ("Nombre del Traductor(a):", "________________________________________________", "Comunidad / Territorio:", "___________________________________"),
        ("Fecha de Traducción:", "_____ / _____ / 202____", "Teléfono / Contacto:", "___________________________________"),
        ("Firma o Aprobación:", "________________________________________________", "Estado de Entrega:", "[   ] Parcial    [   ] Completa")
    ]
    for idx_f, (f1, val1, f2, val2) in enumerate(ficha_items, start=20):
        ws_info.row_dimensions[idx_f].height = 22
        ws_info.cell(row=idx_f, column=1, value=f1).font = Font(name='Calibri', size=9.5, bold=True, color='374151')
        ws_info.cell(row=idx_f, column=2, value=val1).font = Font(name='Calibri', size=9.5, color='4B5563')
        ws_info.cell(row=idx_f, column=4, value=f2).font = Font(name='Calibri', size=9.5, bold=True, color='374151')
        ws_info.cell(row=idx_f, column=5, value=val2).font = Font(name='Calibri', size=9.5, color='4B5563')

    # Agradecimiento Cultural
    ws_info.merge_cells('A24:G24')
    c_agrad = ws_info['A24']
    c_agrad.value = "¡TINGKI PALI! (¡Muchas gracias por su valioso aporte al fortalecimiento y difusión de nuestra lengua originaria!)"
    c_agrad.font = Font(name='Calibri', size=11, bold=True, color='065F46')
    c_agrad.fill = PatternFill(start_color='ECFDF5', end_color='ECFDF5', fill_type='solid')
    c_agrad.alignment = Alignment(horizontal='center', vertical='center')
    ws_info.row_dimensions[24].height = 30

    # Ajuste de anchos en hoja de instrucciones
    ws_info.column_dimensions['A'].width = 28
    ws_info.column_dimensions['B'].width = 34
    ws_info.column_dimensions['C'].width = 4
    ws_info.column_dimensions['D'].width = 26
    ws_info.column_dimensions['E'].width = 30
    ws_info.column_dimensions['F'].width = 16
    ws_info.column_dimensions['G'].width = 16

    # -------------------------------------------------------------------------
    # HOJA 2: PLANTILLA DE TRADUCCIÓN
    # -------------------------------------------------------------------------
    ws_data = wb.create_sheet(title="Plantilla de Traducción")
    ws_data.sheet_properties.tabColor = "107C41"
    ws_data.views.sheetView[0].showGridLines = True

    # Encabezados de Columna
    encabezados = [
        ("REF (Código Técnico)", 23, '1E3A8A', 'FFFFFF'),
        ("Ámbito / Sección", 18, '1E3A8A', 'FFFFFF'),
        ("Ciudad", 16, '1E3A8A', 'FFFFFF'),
        ("Circuito / Recorrido", 25, '1E3A8A', 'FFFFFF'),
        ("Elemento / Hito", 30, '1E3A8A', 'FFFFFF'),
        ("Campo a Traducir", 24, '1E3A8A', 'FFFFFF'),
        ("Texto Original en Español", 55, '1E3A8A', 'FFFFFF'),
        ("Traducción al Miskito (Miskitu bil)", 55, '107C41', 'FFFFFF'),  # Destacado en verde Excel
        ("Estado", 14, '1E3A8A', 'FFFFFF'),
        ("Guía / Indicaciones", 35, '1E3A8A', 'FFFFFF')
    ]

    ws_data.row_dimensions[1].height = 32

    for col_idx, (titulo, ancho, bg_color, fg_color) in enumerate(encabezados, start=1):
        cell = ws_data.cell(row=1, column=col_idx, value=titulo)
        cell.font = Font(name='Calibri', size=10.5, bold=True, color=fg_color)
        cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type='solid')
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = borde_encabezado
        col_letter = get_column_letter(col_idx)
        ws_data.column_dimensions[col_letter].width = ancho

    # Inserción de Filas de Datos
    fill_ref = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid')
    fill_es_normal = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')
    fill_miq_editable = PatternFill(start_color='F0FDF4', end_color='F0FDF4', fill_type='solid')
    fill_pendiente = PatternFill(start_color='FEF2F2', end_color='FEF2F2', fill_type='solid')
    fill_traducido = PatternFill(start_color='ECFDF5', end_color='ECFDF5', fill_type='solid')

    font_ref = Font(name='Consolas', size=9, bold=True, color='334155')
    font_texto = Font(name='Calibri', size=10, color='111827')
    font_miq = Font(name='Calibri', size=10, bold=False, color='065F46')
    font_pendiente = Font(name='Calibri', size=9.5, bold=True, color='DC2626')
    font_traducido = Font(name='Calibri', size=9.5, bold=True, color='16A34A')
    font_guia = Font(name='Calibri', size=8.5, italic=True, color='6B7280')

    for r_idx, item in enumerate(filas_traduccion, start=2):
        # Altura dinámica según extensión del texto en español
        largo_texto = len(item['texto_es'] or "")
        ws_data.row_dimensions[r_idx].height = 48 if largo_texto > 180 else (34 if largo_texto > 70 else 24)

        # 1. REF
        c_ref = ws_data.cell(row=r_idx, column=1, value=item['ref'])
        c_ref.font = font_ref
        c_ref.fill = fill_ref
        c_ref.alignment = Alignment(horizontal='center', vertical='center')
        c_ref.border = borde_fino

        # 2. Ámbito
        c_amb = ws_data.cell(row=r_idx, column=2, value=item['ambito'])
        c_amb.font = font_texto
        c_amb.alignment = Alignment(horizontal='center', vertical='center')
        c_amb.border = borde_fino

        # 3. Ciudad
        c_ciu = ws_data.cell(row=r_idx, column=3, value=item['ciudad'])
        c_ciu.font = Font(name='Calibri', size=10, bold=True, color='1E3A8A')
        c_ciu.alignment = Alignment(horizontal='center', vertical='center')
        c_ciu.border = borde_fino

        # 4. Circuito
        c_cir = ws_data.cell(row=r_idx, column=4, value=item['circuito'])
        c_cir.font = font_texto
        c_cir.alignment = Alignment(horizontal='left', vertical='center')
        c_cir.border = borde_fino

        # 5. Elemento / Hito
        c_ele = ws_data.cell(row=r_idx, column=5, value=item['elemento'])
        c_ele.font = font_texto
        c_ele.alignment = Alignment(horizontal='left', vertical='center')
        c_ele.border = borde_fino

        # 6. Campo
        c_cam = ws_data.cell(row=r_idx, column=6, value=item['campo'])
        c_cam.font = Font(name='Calibri', size=9.5, bold=True, color='374151')
        c_cam.alignment = Alignment(horizontal='left', vertical='center')
        c_cam.border = borde_fino

        # 7. Texto Original en Español
        c_tes = ws_data.cell(row=r_idx, column=7, value=item['texto_es'])
        c_tes.font = font_texto
        c_tes.fill = fill_es_normal
        c_tes.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        c_tes.border = borde_fino

        # 8. Traducción al Miskito (Celda para escribir)
        c_miq = ws_data.cell(row=r_idx, column=8, value=item['texto_miq'])
        c_miq.font = font_miq
        c_miq.fill = fill_miq_editable
        c_miq.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
        c_miq.border = borde_fino

        # 9. Estado
        es_pend = item['es_pendiente']
        c_est = ws_data.cell(row=r_idx, column=9, value="● Pendiente" if es_pend else "✓ Traducido")
        c_est.font = font_pendiente if es_pend else font_traducido
        c_est.fill = fill_pendiente if es_pend else fill_traducido
        c_est.alignment = Alignment(horizontal='center', vertical='center')
        c_est.border = borde_fino

        # 10. Guía
        c_gui = ws_data.cell(row=r_idx, column=10, value=item['guia'])
        c_gui.font = font_guia
        c_gui.alignment = Alignment(horizontal='left', vertical='center')
        c_gui.border = borde_fino

    # En caso de que no haya pendientes y solo_pendientes=True
    if len(filas_traduccion) == 0:
        ws_data.row_dimensions[2].height = 40
        ws_data.merge_cells('A2:J2')
        c_vacio = ws_data['A2']
        c_vacio.value = "✓ ¡EXCELENTE! Todos los contenidos de las ciudades con circuitos ya cuentan con traducción al Miskito."
        c_vacio.font = Font(name='Calibri', size=11, bold=True, color='047857')
        c_vacio.fill = fill_traducido
        c_vacio.alignment = Alignment(horizontal='center', vertical='center')

    # Activación de AutoFilter (Filtros en encabezados) y Freeze Panes (Fijar fila 1)
    ws_data.auto_filter.ref = ws_data.dimensions
    ws_data.freeze_panes = 'A2'

    # Guardar en buffer BytesIO
    buffer_destino = io.BytesIO()
    wb.save(buffer_destino)
    buffer_destino.seek(0)
    return buffer_destino
