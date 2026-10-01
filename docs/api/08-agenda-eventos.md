# 8. Agenda de Eventos y Mural de Publicación

El módulo de eventos permite a usuarios **protagonistas** y **administradores** publicar festividades tradicionales, talleres artesanales, ferias y eventos oficiales de las Ciudades Creativas de Nicaragua. 

Cuenta además con un cálculo automatizado de visibilidad para el **mural de publicación**, activándose automáticamente una cantidad configurable de días antes del inicio del evento.

---

## 8.1 Crear Evento (`POST /api/eventos/`)

* **Endpoint:** `POST /api/eventos/`
* **Headers:**
  * `Content-Type: application/json` *(o `multipart/form-data` si adjunta imagen)*
  * `Authorization: Bearer <JWT_TOKEN>`
  * `X-Company-Id: <ID_EMPRESA>` *(Opcional: Vincula automáticamente el evento a la empresa activa, permitiendo a los miembros del equipo editarlo)*

### Parámetros del Body (JSON)

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `titulo` | `String` | **Sí** | Título de la festividad o evento cultural. |
| `descripcion` | `String` | **Sí** | Detalles de la agenda, exponentes o actividades. |
| `ciudad` | `Integer` | **Sí** | ID de la Ciudad Creativa sede. |
| `empresa` | `Integer` | No | ID de la empresa/taller organizador (opcional). |
| `fecha_inicio` | `Datetime` | **Sí** | Fecha y hora ISO 8601 de inicio (`2026-09-15T10:00:00Z`). |
| `fecha_fin` | `Datetime` | **Sí** | Fecha y hora ISO 8601 de finalización. |
| `ubicacion` | `String` | **Sí** | Dirección, parque o plaza sede. |
| `precio_entrada`| `Decimal` | No | Costo de entrada (`0.00` por defecto). |
| `es_gratuito` | `Boolean` | No | Indica si la entrada es libre (`true` por defecto). |
| `es_oficial` | `Boolean` | No | Indica si está respaldado por alcaldías o instituciones. |
| `dias_previos_mural`| `Integer`| No | Días de anticipación con que aparece en el mural (ej: `10`). |
| `cupo_maximo` | `Integer` | No | Cantidad límite de asistentes (opcional). |
| `solo_este_ano` | `Boolean`| No | Indica si es evento de única vez o recurrente anual. |
| `rango_celebracion` | `String`| No | Descripción textual de recurrencia (ej: "Tercera semana de septiembre"). |

### Ejemplo de Petición
```json
{
  "titulo": "Fiesta Patronal e Hito Cultural de San Jerónimo",
  "descripcion": "Celebración oficial de la ciudad apoyada por la alcaldía y comisión de cultura.",
  "ciudad": 5,
  "empresa": null,
  "fecha_inicio": "2026-09-15T10:00:00Z",
  "fecha_fin": "2026-09-15T18:00:00Z",
  "ubicacion": "Parque Central de Masaya",
  "precio_entrada": "0.00",
  "es_gratuito": true,
  "es_oficial": true,
  "dias_previos_mural": 10,
  "cupo_maximo": 500,
  "solo_este_ano": false,
  "rango_celebracion": "Tercera semana de septiembre (San Jerónimo)"
}
```

### Respuesta Exitosa (`201 Created` / `200 OK`)
```json
{
  "id": 1,
  "creador": 1,
  "creador_username": "admin_alcaldia",
  "empresa": null,
  "empresa_nombre": null,
  "ciudad": 5,
  "ciudad_nombre": "Masaya",
  "titulo": "Fiesta Patronal e Hito Cultural de San Jerónimo",
  "descripcion": "Celebración oficial de la ciudad apoyada por la alcaldía...",
  "solo_este_ano": false,
  "rango_celebracion": "Tercera semana de septiembre (San Jerónimo)",
  "fecha_inicio": "2026-09-15T10:00:00Z",
  "fecha_fin": "2026-09-15T18:00:00Z",
  "ubicacion": "Parque Central de Masaya",
  "latitud": 11.9744,
  "longitud": -86.0942,
  "imagen": null,
  "precio_entrada": "0.00",
  "es_gratuito": true,
  "cupo_maximo": 500,
  "es_oficial": true,
  "dias_previos_mural": 10,
  "en_mural": true,
  "esta_activo": true,
  "total_granos_cafe": 153,
  "user_ha_dado_grano_cafe": false,
  "total_asistentes": 42,
  "user_va_a_asistir": false,
  "galeria": [],
  "publicaciones": [],
  "fecha_creacion": "2026-08-08T08:18:00Z"
}
```

---

## 8.2 Consultar Eventos y Mural de la Ciudad (`GET /api/eventos/`)

Endpoint público con múltiples filtros para alimentar carteleras y calendarios:

```bash
# Filtrar solo eventos activos en la ventana de tiempo del Mural
GET /api/eventos/?en_mural=true

# Filtrar eventos oficiales respaldados por la administración
GET /api/eventos/?es_oficial=true

# Filtrar eventos de una ciudad específica (ej. Masaya ID 5)
GET /api/eventos/?ciudad=5

# Combinación para el mural de una ciudad
GET /api/eventos/?ciudad=5&en_mural=true
```

---

## 8.3 Reaccionar con Grano de Café (`POST /api/eventos/{id}/grano-cafe/`)

Permite al usuario autenticado alternar (dar o retirar) su reacción cultural de **Grano de Café** (icono identitario nicaragüense que sustituye el botón de Like tradicional).

* **Endpoint:** `POST /api/eventos/{id}/grano-cafe/`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Respuesta Exitosa (200 OK):**
```json
{
  "message": "Reacción de grano de café agregada al evento.",
  "ha_dado_grano_cafe": true,
  "total_granos_cafe": 154
}
```

---

## 8.4 Confirmar Asistencia al Evento (`POST /api/eventos/{id}/asistir/`)

Permite a los turistas registrar o revocar su intención de asistencia al evento (`EventoAsistencia`).

* **Endpoint:** `POST /api/eventos/{id}/asistir/`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Respuesta Exitosa (200 OK):**
```json
{
  "message": "Has registrado tu asistencia al evento.",
  "va_a_asistir": true,
  "total_asistentes": 43
}
```

---

[⬅ Módulo de Inversiones](07-modulo-inversiones.md) | [Volver al Índice](README.md) | [Siguiente: Publicaciones y Comentarios ➡](09-publicaciones-comentarios.md)
