"""
Herramientas (Function Calling Tools) para el Asistente Virtual de Ciudades Creativas de Nicaragua.
Cada función está tipada y documentada para que el modelo Gemini pueda seleccionarla y ejecutarla
automáticamente según la consulta del usuario.
"""

import math
from typing import Optional, List, Dict, Any
from django.db.models import Q
from .models import (
    Ciudad,
    CircuitoCreativo,
    PuntoInteres,
    DatoHistorico,
    Evento,
    Empresa,
    OportunidadInversion
)


def _calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia en kilómetros entre dos coordenadas usando la fórmula de Haversine."""
    R = 6371.0  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def buscar_ciudades(nombre: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Busca información general sobre las Ciudades Creativas de Nicaragua (ej. Granada, León, Masaya, Estelí, etc.).
    
    Args:
        nombre: Nombre o parte del nombre de la ciudad a buscar (opcional, si no se especifica lista todas).
    """
    qs = Ciudad.objects.all()
    if nombre:
        qs = qs.filter(Q(nombre__icontains=nombre) | Q(nombre_en__icontains=nombre) | Q(nombre_zh__icontains=nombre))
    
    resultados = []
    for c in qs[:15]:
        resultados.append({
            "id": c.id,
            "nombre": c.nombre,
            "nombre_en": c.nombre_en or c.nombre,
            "nombre_zh": c.nombre_zh or c.nombre,
            "descripcion": c.descripcion,
            "descripcion_en": c.descripcion_en,
            "descripcion_zh": c.descripcion_zh,
            "coordenadas": {
                "latitud": c.latitud_centro,
                "longitud": c.longitud_centro
            },
            "total_circuitos": c.circuitos.count(),
            "total_eventos": c.eventos.filter(esta_activo=True).count(),
            "total_empresas": c.empresas.count(),
        })
    return resultados


def buscar_circuitos(
    ciudad: Optional[str] = None,
    dificultad: Optional[str] = None,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Busca circuitos turísticos y rutas creativas (itinerarios con distancia, duración y dificultad).
    
    Args:
        ciudad: Nombre de la ciudad a la que pertenece el circuito (ej. 'Granada', 'Masaya').
        dificultad: Nivel de dificultad deseado ('Baja', 'Media', 'Alta').
        query: Término de búsqueda libre sobre el nombre o descripción del circuito.
    """
    qs = CircuitoCreativo.objects.select_related('ciudad').prefetch_related('puntos_interes').all()
    
    if ciudad:
        qs = qs.filter(
            Q(ciudad__nombre__icontains=ciudad) |
            Q(ciudad__nombre_en__icontains=ciudad) |
            Q(ciudad__nombre_zh__icontains=ciudad)
        )
    if dificultad:
        qs = qs.filter(dificultad__iexact=dificultad)
    if query:
        qs = qs.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(nombre_en__icontains=query) |
            Q(descripcion_en__icontains=query)
        )
        
    resultados = []
    for cir in qs[:10]:
        puntos = [p.nombre for p in cir.puntos_interes.all()[:5]]
        resultados.append({
            "id": cir.id,
            "nombre": cir.nombre,
            "nombre_en": cir.nombre_en or cir.nombre,
            "nombre_zh": cir.nombre_zh or cir.nombre,
            "ciudad": cir.ciudad.nombre,
            "descripcion": cir.descripcion,
            "distancia_km": float(cir.distancia_km),
            "duracion_estimada": cir.duracion_estimada,
            "dificultad": cir.dificultad,
            "puntos_clave": puntos,
            "total_puntos": cir.puntos_interes.count()
        })
    return resultados


def buscar_puntos_interes(
    ciudad: Optional[str] = None,
    circuito: Optional[str] = None,
    tipo: Optional[str] = None,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Busca puntos de interés específicos (monumentos, talleres artesanales, museos, sitios naturales o gastronómicos).
    
    Args:
        ciudad: Ciudad donde se ubica el punto de interés.
        circuito: Nombre del circuito creativo al que pertenece.
        tipo: Tipo de punto ('Historico', 'Cultural', 'Natural', 'Taller', 'Gastronomico').
        query: Búsqueda libre en el nombre o descripción del punto.
    """
    qs = PuntoInteres.objects.select_related('circuito', 'circuito__ciudad').all()
    
    if ciudad:
        qs = qs.filter(
            Q(circuito__ciudad__nombre__icontains=ciudad) |
            Q(circuito__ciudad__nombre_en__icontains=ciudad)
        )
    if circuito:
        qs = qs.filter(Q(circuito__nombre__icontains=circuito) | Q(circuito__nombre_en__icontains=circuito))
    if tipo:
        qs = qs.filter(tipo__iexact=tipo)
    if query:
        qs = qs.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(nombre_en__icontains=query)
        )
        
    resultados = []
    for p in qs[:15]:
        resultados.append({
            "id": p.id,
            "nombre": p.nombre,
            "nombre_en": p.nombre_en or p.nombre,
            "nombre_zh": p.nombre_zh or p.nombre,
            "tipo": p.tipo,
            "descripcion": p.descripcion,
            "circuito": p.circuito.nombre,
            "ciudad": p.circuito.ciudad.nombre,
            "orden": p.orden,
            "latitud": p.latitud,
            "longitud": p.longitud
        })
    return resultados


def buscar_puntos_cercanos(
    latitud: float,
    longitud: float,
    radio_km: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Encuentra puntos de interés turísticos cercanos a una coordenada GPS (latitud, longitud) reportada por el usuario.
    
    Args:
        latitud: Latitud GPS actual del usuario en formato decimal (ej: 11.9344).
        longitud: Longitud GPS actual del usuario en formato decimal (ej: -85.9560).
        radio_km: Radio máximo de búsqueda en kilómetros (por defecto 5.0 km).
    """
    puntos = PuntoInteres.objects.select_related('circuito', 'circuito__ciudad').all()
    cercanos = []
    
    for p in puntos:
        dist = _calcular_distancia_haversine(latitud, longitud, p.latitud, p.longitud)
        if dist <= radio_km:
            cercanos.append({
                "id": p.id,
                "nombre": p.nombre,
                "tipo": p.tipo,
                "distancia_km": dist,
                "circuito": p.circuito.nombre,
                "ciudad": p.circuito.ciudad.nombre,
                "latitud": p.latitud,
                "longitud": p.longitud,
                "descripcion": p.descripcion[:160] + '...' if len(p.descripcion) > 160 else p.descripcion
            })
            
    cercanos.sort(key=lambda x: x["distancia_km"])
    return cercanos[:10]


def buscar_eventos(
    ciudad: Optional[str] = None,
    activos_solo: bool = True,
    oficiales_solo: Optional[bool] = None,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Busca eventos culturales, ferias artesanales, fiestas patronales y actividades turísticas en las ciudades.
    
    Args:
        ciudad: Nombre de la ciudad del evento.
        activos_solo: Filtrar solo eventos activos (True por defecto).
        oficiales_solo: True para eventos oficiales de la alcaldía/comisión cultural, False para eventos de protagonistas, None para todos.
        query: Búsqueda de texto en título o descripción del evento.
    """
    qs = Evento.objects.select_related('ciudad', 'creador').all()
    
    if activos_solo:
        qs = qs.filter(esta_activo=True)
    if ciudad:
        qs = qs.filter(Q(ciudad__nombre__icontains=ciudad) | Q(ciudad__nombre_en__icontains=ciudad))
    if oficiales_solo is not None:
        qs = qs.filter(es_oficial=oficiales_solo)
    if query:
        qs = qs.filter(Q(titulo__icontains=query) | Q(descripcion__icontains=query))
        
    resultados = []
    for e in qs[:10]:
        resultados.append({
            "id": e.id,
            "titulo": e.titulo,
            "titulo_en": e.titulo_en or e.titulo,
            "titulo_zh": e.titulo_zh or e.titulo,
            "ciudad": e.ciudad.nombre if e.ciudad else "General",
            "descripcion": e.descripcion,
            "fecha_inicio": e.fecha_inicio.strftime('%Y-%m-%d %H:%M'),
            "fecha_fin": e.fecha_fin.strftime('%Y-%m-%d %H:%M') if e.fecha_fin else None,
            "ubicacion": e.ubicacion,
            "precio_entrada": float(e.precio_entrada),
            "es_gratuito": e.es_gratuito,
            "es_oficial": e.es_oficial,
            "total_asistentes": e.total_asistentes
        })
    return resultados


def buscar_empresas(
    ciudad: Optional[str] = None,
    categoria: Optional[str] = None,
    acepta_inversiones: Optional[bool] = None,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Busca empresas turísticas locales, talleres artesanales, restaurantes, hospedajes y destinos turísticos.
    
    Args:
        ciudad: Ciudad donde se ubica la empresa.
        categoria: Categoría de la empresa ('Gastronomia', 'Hospedaje', 'Taller', 'Destino', 'Servicios', 'Otro').
        acepta_inversiones: True para filtrar empresas que buscan inversión turística.
        query: Búsqueda por nombre o descripción de la empresa.
    """
    qs = Empresa.objects.select_related('ciudad').all()
    
    if ciudad:
        qs = qs.filter(Q(ciudad__nombre__icontains=ciudad) | Q(ciudad__nombre_en__icontains=ciudad))
    if categoria:
        qs = qs.filter(categoria__iexact=categoria)
    if acepta_inversiones is not None:
        qs = qs.filter(acepta_inversiones=acepta_inversiones)
    if query:
        qs = qs.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))
        
    resultados = []
    for emp in qs[:10]:
        resultados.append({
            "id": emp.id,
            "nombre": emp.nombre,
            "nombre_en": emp.nombre_en or emp.nombre,
            "nombre_zh": emp.nombre_zh or emp.nombre,
            "categoria": emp.categoria,
            "ciudad": emp.ciudad.nombre if emp.ciudad else None,
            "direccion": emp.direccion,
            "telefono": emp.telefono_contacto,
            "email": emp.email_contacto,
            "sitio_web": emp.sitio_web,
            "acepta_inversiones": emp.acepta_inversiones,
            "descripcion": emp.descripcion
        })
    return resultados


def buscar_datos_historicos(
    ciudad: Optional[str] = None,
    tipo: Optional[str] = None,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Busca hitos históricos, mitos, leyendas, saberes populares y tradiciones culinarias de las ciudades.
    
    Args:
        ciudad: Nombre de la ciudad.
        tipo: Tipo de dato ('Hito', 'Leyenda', 'SaberPopular', 'Gastronomia').
        query: Búsqueda libre en título o contenido.
    """
    qs = DatoHistorico.objects.select_related('ciudad', 'punto_interes').all()
    
    if ciudad:
        qs = qs.filter(
            Q(ciudad__nombre__icontains=ciudad) |
            Q(punto_interes__circuito__ciudad__nombre__icontains=ciudad)
        )
    if tipo:
        qs = qs.filter(tipo__iexact=tipo)
    if query:
        qs = qs.filter(Q(titulo__icontains=query) | Q(contenido__icontains=query))
        
    resultados = []
    for d in qs[:10]:
        ciudad_nombre = d.ciudad.nombre if d.ciudad else (
            d.punto_interes.circuito.ciudad.nombre if d.punto_interes and d.punto_interes.circuito else "General"
        )
        resultados.append({
            "id": d.id,
            "titulo": d.titulo,
            "titulo_en": d.titulo_en or d.titulo,
            "titulo_zh": d.titulo_zh or d.titulo,
            "tipo": d.tipo,
            "epoca_o_ano": d.epoca_o_ano,
            "ciudad": ciudad_nombre,
            "punto_interes": d.punto_interes.nombre if d.punto_interes else None,
            "contenido": d.contenido
        })
    return resultados


def buscar_oportunidades_inversion(
    ciudad: Optional[str] = None,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Busca proyectos y oportunidades de inversión turística y comunitaria disponibles en las empresas locales.
    
    Args:
        ciudad: Ciudad donde se ubica el proyecto de inversión.
        query: Término de búsqueda en título o descripción de la oportunidad.
    """
    qs = OportunidadInversion.objects.select_related('empresa', 'empresa__ciudad').filter(esta_activa=True)
    
    if ciudad:
        qs = qs.filter(Q(empresa__ciudad__nombre__icontains=ciudad) | Q(empresa__ciudad__nombre_en__icontains=ciudad))
    if query:
        qs = qs.filter(Q(titulo__icontains=query) | Q(descripcion__icontains=query))
        
    resultados = []
    for op in qs[:10]:
        resultados.append({
            "id": op.id,
            "titulo": op.titulo,
            "titulo_en": op.titulo_en or op.titulo,
            "titulo_zh": op.titulo_zh or op.titulo,
            "empresa": op.empresa.nombre,
            "ciudad": op.empresa.ciudad.nombre if op.empresa.ciudad else None,
            "monto_requerido": float(op.monto_requerido),
            "monto_minimo_inversion": float(op.monto_minimo_inversion),
            "retorno_estimado": op.retorno_estimado,
            "tipo_inversor_permitido": op.tipo_inversor_permitido,
            "descripcion": op.descripcion
        })
    return resultados


# Lista consolidada de herramientas a registrar en Gemini
TODAS_LAS_HERRAMIENTAS = [
    buscar_ciudades,
    buscar_circuitos,
    buscar_puntos_interes,
    buscar_puntos_cercanos,
    buscar_eventos,
    buscar_empresas,
    buscar_datos_historicos,
    buscar_oportunidades_inversion,
]
