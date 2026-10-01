import math
from django.utils import timezone
from .models import Empresa


def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en metros entre dos puntos geográficos usando la fórmula de Haversine.
    """
    R = 6371000  # Radio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


def obtener_empresas_en_ruta_circuito(circuito, radio_metros=800, radio_patrocinado_metros=5000):
    """
    Obtiene las empresas relevantes para un circuito turístico:
    1. Empresas en la ruta física (orgánicas): Aquellas con coordenadas cuya distancia mínima
       a cualquiera de los puntos de interés del circuito sea <= radio_metros (por defecto 800m).
    2. Empresas con publicidad pagada / patrocinadas: Aquellas que cuenten con pauta activa
       o estén explícitamente vinculadas al circuito, incorporadas con un radio extendido (por defecto 5000m).

    Retorna una lista de empresas decoradas con:
    - es_patrocinada (bool)
    - en_ruta (bool)
    - distancia_metros (float)
    - punto_cercano_nombre (str)

    Orden de presentación:
    1° Empresas patrocinadas (con pauta activa)
    2° Por menor distancia en metros al punto más cercano del circuito.
    """
    puntos = list(circuito.puntos_interes.all())
    if not puntos:
        return []

    # Filtrar empresas de la misma ciudad que tengan coordenadas geográficas registradas
    empresas_candidatas = Empresa.objects.filter(
        ciudad=circuito.ciudad,
        latitud__isnull=False,
        longitud__isnull=False
    ).prefetch_related('circuitos')

    resultado = []
    hoy = timezone.now().date()

    for emp in empresas_candidatas:
        min_dist = float('inf')
        punto_mas_cercano = None

        for p in puntos:
            dist = calcular_distancia_haversine(emp.latitud, emp.longitud, p.latitud, p.longitud)
            if dist < min_dist:
                min_dist = dist
                punto_mas_cercano = p

        if min_dist == float('inf'):
            continue

        # Verificar si la empresa tiene publicidad activa o está vinculada al circuito
        es_patrocinada = False
        if emp.tiene_publicidad:
            if not emp.fecha_fin_publicidad or emp.fecha_fin_publicidad >= hoy:
                es_patrocinada = True

        # O si el administrador la vinculó explícitamente a este circuito
        if not es_patrocinada and emp.circuitos.filter(id=circuito.id).exists():
            es_patrocinada = True

        en_ruta = min_dist <= radio_metros

        # Criterio de incorporación:
        # - Si está físicamente en la ruta (distancia <= radio_metros)
        # - O si pagó publicidad y está en el radio extendido (distancia <= radio_patrocinado_metros)
        if en_ruta or (es_patrocinada and min_dist <= radio_patrocinado_metros):
            emp.es_patrocinada = es_patrocinada
            emp.en_ruta = en_ruta
            emp.distancia_metros = round(min_dist, 1)
            emp.punto_cercano_nombre = punto_mas_cercano.nombre if punto_mas_cercano else None
            resultado.append(emp)

    # Ordenar: primero patrocinadas (True antes que False), luego menor distancia
    resultado.sort(key=lambda x: (not getattr(x, 'es_patrocinada', False), getattr(x, 'distancia_metros', 0)))
    return resultado
