#!/usr/bin/env python3
"""
Script para exportar automáticamente los diagramas ER y UML a formato SVG y PNG
utilizando la API de renderizado de Kroki / Mermaid sin requerir binarios externos de Graphviz.
"""

import os
import base64
import zlib
import urllib.request

DIAGRAMAS = {
    "er_3fn": {
        "tipo": "mermaid",
        "codigo": """
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
        float latitud_centro
        float longitud_centro
    }
    CIRCUITO_CREATIVO {
        int id PK
        int ciudad_id FK
        string nombre
        decimal distancia_km
        string duracion_estimada
        string dificultad
    }
    PUNTO_INTERES {
        int id PK
        int circuito_id FK
        string nombre
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
    }
    GALERIA_MULTIMEDIA {
        int id PK
        int ciudad_id FK
        int punto_interes_id FK
        int evento_id FK
        string titulo
        string tipo
        string imagen
    }
    USUARIO_PUNTO_VISITADO {
        int id PK
        int usuario_id FK
        int punto_interes_id FK
        datetime fecha_visita
        boolean es_validada
        float distancia_metros
    }
    EMPRESA {
        int id PK
        int usuario_id FK
        int ciudad_id FK
        int punto_interes_id FK
        string nombre
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
        boolean esta_activa
    }
    INVERSION_TURISTA {
        int id PK
        int inversionista_id FK
        int oportunidad_id FK
        decimal monto_propuesto
        string tipo_inversor
        string estado
    }
    EVENTO {
        int id PK
        int creador_id FK
        int empresa_id FK
        int ciudad_id FK
        string titulo
        datetime fecha_inicio
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
    }

    CIUDAD ||--o{ CIRCUITO_CREATIVO : posee
    CIUDAD ||--o{ DATO_HISTORICO : documenta
    CIUDAD ||--o{ EMPRESA : radica_en
    CIUDAD ||--o{ EVENTO : organiza
    CIRCUITO_CREATIVO ||--|{ PUNTO_INTERES : contiene
    PUNTO_INTERES ||--o{ DATO_HISTORICO : tiene_contexto
    PUNTO_INTERES ||--o{ GALERIA_MULTIMEDIA : contiene_fotos
    PUNTO_INTERES ||--o{ USUARIO_PUNTO_VISITADO : recibe_visitas
    PUNTO_INTERES ||--o{ EMPRESA : alberga
    AUTH_USER ||--o{ USUARIO_PUNTO_VISITADO : registra
    AUTH_USER ||--o{ EMPRESA : administra
    AUTH_USER ||--o{ INVERSION_TURISTA : invierte
    AUTH_USER ||--o{ EVENTO : crea
    AUTH_USER ||--o{ EVENTO_ASISTENCIA : confirma
    AUTH_USER ||--o{ PUBLICACION : publica
    EMPRESA ||--o{ OPORTUNIDAD_INVERSION : oferta
    EMPRESA ||--o{ EVENTO : patrocina
    OPORTUNIDAD_INVERSION ||--o{ INVERSION_TURISTA : recibe
    EVENTO ||--o{ EVENTO_ASISTENCIA : registra
    EVENTO ||--o{ GALERIA_MULTIMEDIA : documenta
    PUBLICACION ||--|{ PUBLICACION_IMAGEN : incluye
    PUBLICACION ||--o{ COMENTARIO_PUBLICACION : tiene
"""
    },
    "uml_clases": {
        "tipo": "mermaid",
        "codigo": """
classDiagram
    direction TB
    class AbstractUser {
        +String username
        +String email
    }
    class User {
        +Boolean es_protagonista
        +Boolean es_turista
        +String telefono
        +ImageField foto_perfil
    }
    class Ciudad {
        +String nombre
        +Float latitud_centro
        +Float longitud_centro
    }
    class CircuitoCreativo {
        +String nombre
        +Decimal distancia_km
        +String duracion_estimada
        +String dificultad
    }
    class PuntoInteres {
        +String nombre
        +String tipo
        +Integer orden
        +Float latitud
        +Float longitud
    }
    class Empresa {
        +String nombre
        +String categoria
        +Boolean acepta_inversiones
    }
    class OportunidadInversion {
        +String titulo
        +Decimal monto_requerido
        +Decimal monto_minimo_inversion
        +Decimal monto_recaudado
    }
    class InversionTurista {
        +Decimal monto_propuesto
        +String tipo_inversor
        +String estado
    }
    class Evento {
        +String titulo
        +DateTime fecha_inicio
        +Boolean es_oficial
        +en_mural() Boolean
        +total_asistentes() Integer
    }
    class UsuarioPuntoVisitado {
        +DateTime fecha_visita
        +Boolean es_validada
        +Float distancia_metros
    }
    class Publicacion {
        +String titulo
        +Boolean esta_activa
        +total_likes() Integer
    }

    AbstractUser <|-- User
    Ciudad "1" *-- "0..*" CircuitoCreativo : circuitos
    CircuitoCreativo "1" *-- "1..*" PuntoInteres : puntos
    User "1" <-- "0..*" Empresa : gestiona
    Ciudad "1" <-- "0..*" Empresa : ubica
    Empresa "1" *-- "0..*" OportunidadInversion : ofrece
    OportunidadInversion "1" o-- "0..*" InversionTurista : recibe
    User "1" <-- "0..*" InversionTurista : invierte
    User "1" <-- "0..*" Evento : crea
    Ciudad "0..1" <-- "0..*" Evento : sede
    User "1" <-- "0..*" UsuarioPuntoVisitado : visita
    PuntoInteres "1" <-- "0..*" UsuarioPuntoVisitado : visitado
    User "1" <-- "0..*" Publicacion : publica
"""
    },
    "uml_casos_uso": {
        "tipo": "mermaid",
        "codigo": """
flowchart TD
    subgraph ACTORES [" 👥 Actores "]
        T["🚶‍♂️ Turista / Visitante"]
        P["🎨 Protagonista / Negocio"]
        INV["💼 Inversionista Estratégico"]
        ADM["🏛️ Administrador / Alcaldía"]
    end

    subgraph SISTEMA [" 🏛️ CodiseCore (Circuitos Creativos) "]
        CU1["CU01: Explorar Ciudades y Circuitos"]
        CU2["CU02: Visualizar Mapa Interactivo"]
        CU3["CU03: Validar Visita GPS al Punto"]
        CU4["CU04: Confirmar Asistencia a Evento"]
        CU5["CU05: Apoyar con Granos de Café"]
        CU6["CU06: Publicar en Feed Comunitario"]
        CU7["CU07: Gestionar Perfil de Empresa/Taller"]
        CU8["CU08: Publicar Evento Cultural"]
        CU9["CU09: Crear Oportunidad de Inversión"]
        CU10["CU10: Aprobar / Rechazar Inversiones"]
        CU11["CU11: Postular Oferta de Inversión"]
        CU12["CU12: Marcar Evento como Oficial"]
        CU13["CU13: Auditar Métricas de Impacto"]
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
"""
    },
    "uml_actividades": {
        "tipo": "mermaid",
        "codigo": """
stateDiagram-v2
    [*] --> AbrirCircuito: Turista abre circuito creativo
    AbrirCircuito --> SeleccionarPunto: Turista selecciona punto en mapa
    SeleccionarPunto --> ObtenerGPS: App solicita coordenadas GPS del dispositivo
    
    state "Verificación de Rango Geográfico" as VerifGPS <<choice>>
    ObtenerGPS --> VerifGPS: Calcula distancia euclidiana / Haversine
    
    VerifGPS --> VisitaInvalida: Distancia > 50 metros
    VerifGPS --> RegistrarVisita: Distancia <= 50 metros
    
    VisitaInvalida --> NotificarUsuario: "No estás dentro del perímetro del punto"
    NotificarUsuario --> SeleccionarPunto
    
    RegistrarVisita --> GuardarEnBD: Insertar en UsuarioPuntoVisitado (es_validada=True)
    GuardarEnBD --> DesbloquearInsignia: Otorgar reconocimiento de ruta
    DesbloquearInsignia --> PermitirResena: Habilitar opción de calificar/comentar
    PermitirResena --> [*]
"""
    }
}

def render_kroki(codigo: str, tipo: str, formato: str = "svg") -> bytes:
    """Envía el código a la API de Kroki para renderizado vectorial directo."""
    compressed = zlib.compress(codigo.encode('utf-8'), 9)
    encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
    url = f"https://kroki.io/{tipo}/{formato}/{encoded}"
    req = urllib.request.Request(url, headers={'User-Agent': 'CodiseCore-Diagrams/1.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()

def main():
    output_dir = "docs_diagramas"
    os.makedirs(output_dir, exist_ok=True)
    print(f"🚀 Generando diagramas en la carpeta: '{output_dir}/'...")

    for nombre, datos in DIAGRAMAS.items():
        print(f"  ⏳ Procesando '{nombre}' ({datos['tipo']})...")
        try:
            # Generar SVG
            svg_data = render_kroki(datos["codigo"], datos["tipo"], "svg")
            svg_path = os.path.join(output_dir, f"{nombre}.svg")
            with open(svg_path, "wb") as f:
                f.write(svg_data)
            print(f"     ✅ Guardado SVG: {svg_path}")

            # Generar PNG
            png_data = render_kroki(datos["codigo"], datos["tipo"], "png")
            png_path = os.path.join(output_dir, f"{nombre}.png")
            with open(png_path, "wb") as f:
                f.write(png_data)
            print(f"     ✅ Guardado PNG: {png_path}")
        except Exception as e:
            print(f"     ⚠️ Error renderizando {nombre} vía API: {e}")

    print("\n🎉 Proceso finalizado. Diagramas listos para usar en documentación y reportes.")

if __name__ == "__main__":
    main()
