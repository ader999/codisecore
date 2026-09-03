# 📐 Diagramación de Base de Datos (ER 3FN) y UML Completos
**Proyecto:** CodiseCore / Circuitos Creativos de Nicaragua  
**Framework:** Django 6.0 + Django REST Framework  
**Normalización:** Tercera Forma Normal (3FN)

---

## 📑 Tabla de Contenidos
1. [1. Diagrama Entidad-Relación Normalizado (3FN)](#1-diagrama-entidad-relación-normalizado-3fn)
2. [2. Diagrama de Clases UML](#2-diagrama-de-clases-uml)
3. [3. Diagrama de Casos de Uso UML](#3-diagrama-de-casos-de-uso-uml)
4. [4. Diagrama de Actividades UML (Flujos de Negocio)](#4-diagrama-de-actividades-uml-flujos-de-negocio)
5. [5. Guía de Exportación y Herramientas Python](#5-guía-de-exportación-y-herramientas-python)

---

## 1. Diagrama Entidad-Relación Normalizado (3FN)

El modelo de datos cumple con las reglas de la **Tercera Forma Normal (3FN)**:
- **1FN:** Atributos atómicos en todas las columnas.
- **2FN:** Dependencia total de la clave primaria.
- **3FN:** Eliminación de dependencias transitivas mediante claves foráneas explícitas.

```mermaid
erDiagram
    AUTH_USER {
        int id PK
        string username
        string email
        boolean es_protagonista
        boolean es_turista
        string telefono
        string foto_perfil
    }
    CIUDAD {
        int id PK
        string nombre UK
        text descripcion
        string imagen_portada
        float latitud_centro
        float longitud_centro
    }
    CIRCUITO_CREATIVO {
        int id PK
        int ciudad_id FK
        string nombre
        text descripcion
        decimal distancia_km
        string duracion_estimada
        string dificultad
    }
    PUNTO_INTERES {
        int id PK
        int circuito_id FK
        string nombre
        text descripcion
        string tipo
        int orden
        float latitud
        float longitud
    }
    DATO_HISTORICO {
        int id PK
        int ciudad_id FK
        int punto_interes_id FK
        string titulo
        string tipo
        text contenido
        string epoca_o_ano
    }
    GALERIA_MULTIMEDIA {
        int id PK
        int ciudad_id FK
        int punto_interes_id FK
        int evento_id FK
        string titulo
        string tipo
        string imagen
        string video_url
    }
    USUARIO_PUNTO_VISITADO {
        int id PK
        int usuario_id FK
        int punto_interes_id FK
        datetime fecha_visita
        float latitud_usuario
        float longitud_usuario
        boolean es_validada
        float distancia_metros
    }
    EMPRESA {
        int id PK
        int usuario_id FK
        int ciudad_id FK
        int punto_interes_id FK
        string nombre
        text descripcion
        string categoria
        boolean acepta_inversiones
    }
    OPORTUNIDAD_INVERSION {
        int id PK
        int empresa_id FK
        string titulo
        decimal monto_requerido
        decimal monto_minimo_inversion
        decimal monto_recaudado
        string retorno_estimado
        string tipo_inversor_permitido
        boolean esta_activa
    }
    INVERSION_TURISTA {
        int id PK
        int inversionista_id FK
        int oportunidad_id FK
        decimal monto_propuesto
        string tipo_inversor
        string estado
        datetime fecha_solicitud
    }
    EVENTO {
        int id PK
        int creador_id FK
        int empresa_id FK
        int ciudad_id FK
        string titulo
        datetime fecha_inicio
        datetime fecha_fin
        string ubicacion
        boolean es_oficial
        boolean esta_activo
    }
    EVENTO_ASISTENCIA {
        int id PK
        int usuario_id FK
        int evento_id FK
        datetime fecha_registro
    }
    PUBLICACION {
        int id PK
        int autor_id FK
        int empresa_id FK
        int ciudad_id FK
        int evento_id FK
        string titulo
        text descripcion
        boolean esta_activa
    }
    PUBLICACION_IMAGEN {
        int id PK
        int publicacion_id FK
        string imagen
    }
    COMENTARIO_PUBLICACION {
        int id PK
        int publicacion_id FK
        int autor_id FK
        text contenido
        boolean esta_activo
    }

    CIUDAD ||--o{ CIRCUITO_CREATIVO : "posee"
    CIUDAD ||--o{ DATO_HISTORICO : "documenta"
    CIUDAD ||--o{ EMPRESA : "radica_en"
    CIUDAD ||--o{ EVENTO : "organiza"
    CIRCUITO_CREATIVO ||--|{ PUNTO_INTERES : "contiene"
    PUNTO_INTERES ||--o{ DATO_HISTORICO : "tiene_contexto"
    PUNTO_INTERES ||--o{ GALERIA_MULTIMEDIA : "contiene_fotos"
    PUNTO_INTERES ||--o{ USUARIO_PUNTO_VISITADO : "recibe_visitas"
    PUNTO_INTERES ||--o{ EMPRESA : "alberga"
    AUTH_USER ||--o{ USUARIO_PUNTO_VISITADO : "registra"
    AUTH_USER ||--o{ EMPRESA : "administra"
    AUTH_USER ||--o{ INVERSION_TURISTA : "invierte"
    AUTH_USER ||--o{ EVENTO : "crea"
    AUTH_USER ||--o{ EVENTO_ASISTENCIA : "confirma"
    AUTH_USER ||--o{ PUBLICACION : "publica"
    EMPRESA ||--o{ OPORTUNIDAD_INVERSION : "oferta"
    EMPRESA ||--o{ EVENTO : "patrocina"
    OPORTUNIDAD_INVERSION ||--o{ INVERSION_TURISTA : "recibe"
    EVENTO ||--o{ EVENTO_ASISTENCIA : "registra"
    EVENTO ||--o{ GALERIA_MULTIMEDIA : "documenta"
    PUBLICACION ||--|{ PUBLICACION_IMAGEN : "incluye"
    PUBLICACION ||--o{ COMENTARIO_PUBLICACION : "tiene"
```

---

## 2. Diagrama de Clases UML

Representa la estructura orientada a objetos del sistema en Django, reflejando herencias de `models.Model`, métodos de dominio, atributos tipados y propiedades calculadas (`@property`).

```mermaid
classDiagram
    direction TB

    class AbstractUser {
        <<Abstract>>
        +String username
        +String email
        +String password
        +Boolean is_active
    }

    class User {
        +Boolean es_protagonista
        +Boolean es_turista
        +String telefono
        +ImageField foto_perfil
        +__str__() String
    }

    class Ciudad {
        +String nombre
        +String descripcion
        +Float latitud_centro
        +Float longitud_centro
        +__str__() String
    }

    class CircuitoCreativo {
        +String nombre
        +Decimal distancia_km
        +String duracion_estimada
        +String dificultad
        +__str__() String
    }

    class PuntoInteres {
        +String nombre
        +String tipo
        +Integer orden
        +Float latitud
        +Float longitud
        +__str__() String
    }

    class Empresa {
        +String nombre
        +String categoria
        +String direccion
        +Boolean acepta_inversiones
        +__str__() String
    }

    class OportunidadInversion {
        +String titulo
        +Decimal monto_requerido
        +Decimal monto_minimo_inversion
        +Decimal monto_recaudado
        +Boolean esta_activa
        +__str__() String
    }

    class InversionTurista {
        +Decimal monto_propuesto
        +String tipo_inversor
        +String estado
        +DateTime fecha_solicitud
        +__str__() String
    }

    class Evento {
        +String titulo
        +DateTime fecha_inicio
        +DateTime fecha_fin
        +Boolean es_oficial
        +en_mural() Boolean
        +total_granos_cafe() Integer
        +total_asistentes() Integer
        +__str__() String
    }

    class UsuarioPuntoVisitado {
        +DateTime fecha_visita
        +Boolean es_validada
        +Float distancia_metros
        +__str__() String
    }

    class Publicacion {
        +String titulo
        +String descripcion
        +Boolean esta_activa
        +total_likes() Integer
        +total_comentarios() Integer
        +__str__() String
    }

    AbstractUser <|-- User
    Ciudad "1" *-- "0..*" CircuitoCreativo : circuitos
    CircuitoCreativo "1" *-- "1..*" PuntoInteres : puntos_interes
    Empresa "0..*" --> "1" User : gestionada_por
    Empresa "0..*" --> "1" Ciudad : ubicada_en
    Empresa "1" *-- "0..*" OportunidadInversion : ofrece
    OportunidadInversion "1" o-- "0..*" InversionTurista : recibe
    InversionTurista "0..*" --> "1" User : postulada_por
    Evento "0..*" --> "1" User : creado_por
    Evento "0..*" --> "0..1" Ciudad : sede
    UsuarioPuntoVisitado "0..*" --> "1" User : visitado_por
    UsuarioPuntoVisitado "0..*" --> "1" PuntoInteres : punto
    Publicacion "0..*" --> "1" User : publicada_por
```

---

## 3. Diagrama de Casos de Uso UML

```mermaid
flowchart TD
    subgraph ACTORES[Actores del Sistema]
        T[Turista / Visitante]
        P[Protagonista / Negocio]
        INV[Inversionista Estratégico]
        ADM[Administrador / Alcaldía]
    end

    subgraph SISTEMA[CodiseCore - Circuitos Creativos]
        CU1[CU01: Explorar Ciudades y Circuitos]
        CU2[CU02: Visualizar Mapa Interactivo]
        CU3[CU03: Validar Visita GPS al Punto]
        CU4[CU04: Confirmar Asistencia a Evento]
        CU5[CU05: Apoyar con Granos de Café]
        CU6[CU06: Publicar en Feed Comunitario]
        
        CU7[CU07: Gestionar Perfil de Empresa]
        CU8[CU08: Publicar Evento Cultural]
        CU9[CU09: Crear Oportunidad de Inversión]
        CU10[CU10: Gestionar Inversiones]
        
        CU11[CU11: Postular Oferta de Inversión]
        
        CU12[CU12: Marcar Evento como Oficial]
        CU13[CU13: Auditar Métricas de Impacto]
    end

    T --> CU1
    T --> CU2
    T --> CU3
    T --> CU4
    T --> CU5
    T --> CU6

    P --> CU7
    P --> CU8
    P --> CU9
    P --> CU10
    P --> CU6

    INV --> CU1
    INV --> CU11

    ADM --> CU12
    ADM --> CU13

    CU2 -.->|include| CU1
    CU3 -.->|extend| CU2
    CU11 -.->|include| CU9
```

---

## 4. Diagrama de Actividades UML (Flujos de Negocio)

### Actividad A: Validación de Visita a Punto de Interés por GPS

```mermaid
stateDiagram-v2
    state VerifGPS <<choice>>

    [*] --> AbrirCircuito : Turista abre circuito creativo
    AbrirCircuito --> SeleccionarPunto : Selecciona punto en mapa
    SeleccionarPunto --> ObtenerGPS : App solicita coordenadas GPS
    ObtenerGPS --> VerifGPS : Calcula distancia Haversine
    
    VerifGPS --> VisitaInvalida : Distancia > 50m
    VerifGPS --> RegistrarVisita : Distancia <= 50m
    
    VisitaInvalida --> NotificarUsuario : Fuera de perimetro
    NotificarUsuario --> SeleccionarPunto
    
    RegistrarVisita --> GuardarEnBD : Insertar en BD (es_validada=True)
    GuardarEnBD --> DesbloquearInsignia : Otorgar reconocimiento
    DesbloquearInsignia --> PermitirResena : Habilitar calificacion
    PermitirResena --> [*]
```

---

## 5. Guía de Exportación y Herramientas Python

1. **Visor Interactivo:** Abre el archivo [diagramas_visor.html](file:///home/overader/Proyectos/python/Django/codisecore/diagramas_visor.html) directamente en tu navegador para interactuar con zoom, pan y descarga en formato SVG.
2. **Generación directa de archivo DOT:**
   ```bash
   python manage.py graph_models codiselu -o diagram_er.dot
   ```
