# 4. Catálogo Turístico (Ciudades, Circuitos y Puntos de Interés)

El catálogo turístico constituye el núcleo de consulta de información cultural y geográfica de la Red de Ciudades Creativas de Nicaragua. Está optimizado para que clientes móviles y frontend puedan obtener toda la jerarquía de datos en una sola petición optimizada.

---

## 4.1 Endpoints del Catálogo

| Endpoint | Método | Descripción |
| :--- | :---: | :--- |
| `GET /api/ciudades/` | `GET` | Lista las 10 Ciudades Creativas con sus circuitos, puntos, leyendas y galerías anidadas. |
| `GET /api/ciudades/{id}/` | `GET` | Detalle completo de una ciudad específica por su ID. |
| `GET /api/circuitos/` | `GET` | Lista de circuitos creativos turísticos. Filtro opcional: `?ciudad={id}`. |
| `GET /api/circuitos/{id}/empresas/`| `GET` | Lista las empresas recomendadas en el circuito (en ruta <= 800m y patrocinadas <= 5000m). |
| `GET /api/puntos-interes/` | `GET` | Puntos de interés con coordenadas GPS. Filtros: `?circuito={id}`, `?ciudad={id}`, `?ids=1,2,5`. |
| `GET /api/datos-historicos/`| `GET` | Historias, mitos, leyendas y saberes populares. Filtro: `?ciudad={id}`, `?punto={id}`. |
| `GET /api/galeria-multimedia/`| `GET`| Colección de fotos y videos turísticos. |

---

## 4.2 Estructura de Respuesta JSON Anidada (`GET /api/ciudades/`)

Al consumir el endpoint de ciudades, la respuesta incluye automáticamente toda la información anidada para renderizar en mapas interactivos y pantallas de detalle sin necesidad de múltiples llamadas de red:

```json
[
  {
    "id": 1,
    "nombre": "León",
    "descripcion": "Ciudad universitaria y capital cultural, cuna de poetas y arquitectura colonial.",
    "imagen_portada": "http://localhost:8000/media/ciudades/leon_portada.jpg",
    "latitud_centro": 12.4379,
    "longitud_centro": -86.878,
    "circuitos": [
      {
        "id": 1,
        "ciudad": 1,
        "ciudad_nombre": "León",
        "nombre": "Ruta de los Poetas y Murales Históricos",
        "descripcion": "Un recorrido caminando por la arquitectura colonial...",
        "distancia_km": "3.20",
        "duracion_estimada": "2 horas",
        "dificultad": "Baja",
        "imagen_mapa": "http://localhost:8000/media/circuitos/mapa_leon.jpg",
        "puntos_interes": [
          {
            "id": 1,
            "circuito": 1,
            "circuito_nombre": "Ruta de los Poetas y Murales Históricos",
            "nombre": "Insigne y Real Basílica Catedral de León",
            "descripcion": "Patrimonio de la Humanidad por la UNESCO...",
            "tipo": "Historico",
            "orden": 1,
            "latitud": 12.435,
            "longitud": -86.879,
            "datos_historicos": [
              {
                "id": 3,
                "ciudad": null,
                "punto_interes": 1,
                "titulo": "Tumba del Poeta Rubén Darío en la Catedral",
                "tipo": "Hito",
                "contenido": "Bajo la estatua de un león doliente...",
                "epoca_o_ano": "1916"
              }
            ],
            "galeria": [
              {
                "id": 10,
                "tipo": "Imagen",
                "imagen": "http://localhost:8000/media/galeria/catedral_fachada.jpg",
                "video_url": null
              }
            ]
          }
        ],
        "empresas_en_ruta": [
          {
            "id": 4,
            "nombre": "Restaurante El Portal Colonial",
            "categoria": "Gastronomia",
            "direccion": "Costado norte de la plaza",
            "telefono_contacto": "+50588882222",
            "numero_whatsapp": "+50588882222",
            "link_whatsapp": "https://wa.me/50588882222",
            "imagen_portada": "http://localhost:8000/media/empresas/portal.jpg",
            "latitud": 12.4450,
            "longitud": -86.8900,
            "es_patrocinada": true,
            "en_ruta": false,
            "distancia_metros": 1450.0,
            "punto_cercano_nombre": "Insigne y Real Basílica Catedral de León"
          },
          {
            "id": 1,
            "nombre": "Taller El Poeta",
            "categoria": "Taller",
            "direccion": "Calle peatonal",
            "telefono_contacto": "+50588881111",
            "numero_whatsapp": "+50588881111",
            "link_whatsapp": "https://wa.me/50588881111",
            "imagen_portada": null,
            "latitud": 12.4353,
            "longitud": -86.8792,
            "es_patrocinada": false,
            "en_ruta": true,
            "distancia_metros": 39.8,
            "punto_cercano_nombre": "Insigne y Real Basílica Catedral de León"
          }
        ]
      }
    ],
    "datos_historicos": [
      {
        "id": 1,
        "ciudad": 1,
        "punto_interes": null,
        "titulo": "Fundación de León y Traslado desde León Viejo",
        "tipo": "Hito",
        "contenido": "Tras la erupción del volcán Momotombo...",
        "epoca_o_ano": "1610"
      },
      {
        "id": 2,
        "ciudad": 1,
        "punto_interes": null,
        "titulo": "La Gigantona y el Pepe Cabezón",
        "tipo": "Leyenda",
        "contenido": "Expresión folclórica y satírica...",
        "epoca_o_ano": "Época Colonial"
      }
    ],
    "galeria": [
      {
        "id": 1,
        "ciudad": 1,
        "punto_interes": null,
        "titulo": "Panorámica del Centro Histórico de León",
        "tipo": "Imagen",
        "imagen": "http://localhost:8000/media/galeria/imagenes/leon_centro.jpg",
        "video_archivo": null,
        "video_url": null
      },
      {
        "id": 2,
        "ciudad": 1,
        "punto_interes": null,
        "titulo": "Documental: León, Cuna de la Revolución y Poesía",
        "tipo": "Video",
        "imagen": null,
        "video_archivo": "http://localhost:8000/media/galeria/videos/leon_doc.mp4",
        "video_url": "https://www.youtube.com/watch?v=ejemplo_leon_creativo"
      }
    ]
  }
]
```

---

## 4.3 Consultas Optimizadas para Mapas Móviles

Para pintar marcadores en el mapa sin descargar toda la información pesada de historias o videos:

```bash
# Consultar puntos de interés de una ciudad específica
GET /api/puntos-interes/?ciudad=1

# Consultar puntos pertenecientes a un circuito turístico específico
GET /api/puntos-interes/?circuito=2

# Consultar un lote específico de puntos por ID
GET /api/puntos-interes/?ids=1,3,7,12
```

---

[⬅ Resumen de Endpoints](03-resumen-endpoints.md) | [Volver al Índice](README.md) | [Siguiente: Visitas y Geolocalización ➡](05-visitas-geolocalizacion.md)
