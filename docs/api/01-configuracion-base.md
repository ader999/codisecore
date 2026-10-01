# 1. Configuración Base de la API

Este módulo detalla los parámetros de red, límites de subida de archivos multimedia y el sistema de localización multi-idioma de la API REST de **Ciudades Creativas de Nicaragua**.

---

## 1.1 Direcciones y Formatos

* **URL Base de Desarrollo:** `http://localhost:8000/api/`
* **URL en Emulador Android:** `http://10.0.2.2:8000/api/`
* **URL de Producción:** Dominio configurado con SSL/TLS (`https://tudominio.com/api/`).
* **Formato de datos estándar:** `JSON` (`Content-Type: application/json`).
* **Formato de carga de archivos (imágenes/multimedia):** `multipart/form-data`.

---

## 1.2 Configuración del Servidor y Carga Masiva de Multimedia

Para soportar la subida masiva de imágenes (hasta **10 fotografías por publicación**) en redes móviles o conexiones de baja velocidad sin experimentar errores como `413 Request Entity Too Large` o `stream was reset: CANCEL`, el stack de infraestructura está calibrado con los siguientes límites:

### Servidor Web / Nginx Reverse Proxy (`nginx/default.conf`)
* `client_max_body_size 50M;`: Permite peticiones de cuerpo multipart de hasta 50 Megabytes.
* `proxy_read_timeout 300s;` / `client_body_timeout 300s;`: Tiempos de espera extendidos a 300 segundos (5 minutos) para evitar caídas de conexión durante la transmisión de fotos en alta resolución en redes celulares.

### Backend Django (`codiselu/settings.py`)
* `DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800` (50 MB).
* `FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400` (25 MB).
* `DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000`.

### Servidor de Aplicación Gunicorn (`Dockerfile`)
* `--timeout 300`: Mantiene activos los workers de procesamiento durante la ingesta y redimensionamiento de archivos pesados.

---

## 1.3 Soporte Multi-idioma (Español, Inglés y Chino Mandarín)

La API cuenta con traducción automática de contenido dinámico (Ciudades, Circuitos, Puntos de Interés, Eventos, Empresas, Oportunidades de Inversión y Datos Históricos) para turistas internacionales.

### ¿Cómo solicitar el idioma desde la App Móvil o Web?
Existen dos formas estándar y totalmente compatibles:

#### 1. Vía Cabecera HTTP `Accept-Language` (Recomendado)
* **Inglés:** `Accept-Language: en`
* **Mandarín:** `Accept-Language: zh` o `Accept-Language: zh-CN` o `Accept-Language: zh-Hans`
* **Español:** `Accept-Language: es` (o sin cabecera por defecto)

#### 2. Vía Parámetro Query en la URL (`?lang=` o `?idioma=`)
* **Inglés:** `GET /api/ciudades/?lang=en`
* **Mandarín:** `GET /api/ciudades/?lang=zh`
* **Español:** `GET /api/ciudades/?lang=es`

### Formato de Respuesta Multi-idioma
Los campos principales (`nombre`, `descripcion`, `titulo`, `contenido`, `ciudad_nombre`, etc.) se transforman automáticamente al idioma solicitado sin alterar los nombres de las claves JSON. Además, se incluye el nodo `traducciones` con los 3 idiomas por si el cliente móvil o web desea almacenarlos en caché local:

```json
{
  "id": 1,
  "nombre": "Colonial Granada",
  "descripcion": "Beautiful colonial city on the shores of the Great Lake of Nicaragua.",
  "latitud_centro": 11.9299,
  "longitud_centro": -85.9560,
  "traducciones": {
    "es": {
      "nombre": "Granada Colonial",
      "descripcion": "Hermosa ciudad colonial a orillas del Gran Lago de Nicaragua."
    },
    "en": {
      "nombre": "Colonial Granada",
      "descripcion": "Beautiful colonial city on the shores of the Great Lake of Nicaragua."
    },
    "zh": {
      "nombre": "殖民地格拉纳达",
      "descripcion": "尼加拉瓜大湖畔美丽的殖民城市。"
    }
  }
}
```

---

[⬅ Volver al Índice de la API](README.md) | [Siguiente: Autenticación (JWT y Google) ➡](02-autenticacion-jwt-google.md)
