# Guía de Conexión a la API: Ciudades Creativas de Nicaragua

Esta guía explica cómo conectarse a la API REST del proyecto desde cualquier cliente (**Frontend Web, App Móvil (Kotlin / Android Nativo), Postman o Python**) para obtener la información de las 10 Ciudades Creativas, sus Circuitos, Puntos de Interés, Datos Históricos, Galería Multimedia, Empresas, Oportunidades de Inversión y Eventos.

---

## 1. Configuración Base

* **URL Base de la API:** `http://localhost:8000/api/` *(Reemplazar `localhost:8000` por el dominio o IP de producción si aplica)*.
* **Formato de datos estándar:** `JSON` (`Content-Type: application/json`).
* **Formato de carga de archivos (imágenes/multimedia):** `multipart/form-data`.

### 1.1 Configuración de Servidor y Subida de Múltiples Imágenes
Para soportar la subida masiva de imágenes (hasta **10 fotos por publicación**) en redes móviles lentas sin experimentar errores como `413 Request Entity Too Large` o `stream was reset: CANCEL`, el servidor está configurado con los siguientes límites:

* **Servidor Web / Nginx Reverse Proxy (`nginx/default.conf`):**
  * `client_max_body_size 50M;`: Permite peticiones de cuerpo multipart de hasta 50 MB.
  * `proxy_read_timeout 300s;` / `client_body_timeout 300s;`: Tiempos de espera extendidos a 300 segundos (5 minutos) para evitar caídas de conexión durante la transmisión en red móvil.
* **Backend Django (`codiselu/settings.py`):**
  * `DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800` (50 MB).
  * `FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400` (25 MB).
  * `DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000`.
* **Gunicorn Application Server (`Dockerfile`):**
  * `--timeout 300`: Mantiene los workers ejecutando durante cargas de archivos grandes.

### 1.2 Soporte Multi-idioma (Español, Inglés y Chino Mandarín)
La API cuenta con traducción automática de contenido dinámico (Ciudades, Circuitos, Puntos de Interés, Eventos, Empresas, Oportunidades de Inversión y Datos Históricos) para turistas internacionales.

#### ¿Cómo solicitar el idioma desde la App Móvil o Web?
Existen dos formas estándar y totalmente compatibles:

1. **Vía Cabecera HTTP `Accept-Language` (Recomendado):**
   * Inglés: `Accept-Language: en`
   * Mandarín: `Accept-Language: zh` o `Accept-Language: zh-CN` o `Accept-Language: zh-Hans`
   * Español: `Accept-Language: es` (o sin cabecera)

2. **Vía Parámetro Query en la URL (`?lang=` o `?idioma=`):**
   * Inglés: `GET /api/ciudades/?lang=en`
   * Mandarín: `GET /api/ciudades/?lang=zh`
   * Español: `GET /api/ciudades/?lang=es`

#### Formato de Respuesta
Los campos principales (`nombre`, `descripcion`, `titulo`, `contenido`, `ciudad_nombre`, etc.) se transforman automáticamente al idioma solicitado sin alterar los nombres de las claves JSON. Además, se incluye el nodo `traducciones` con los 3 idiomas por si la app móvil desea cachearlos localmente:

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

## 2. Autenticación (JWT - JSON Web Tokens)

Aunque los endpoints de consulta pública de ciudades y circuitos no requieren autenticación, para realizar acciones protegidas (como perfil de usuario, registro de visitas o creación de empresas/inversiones/eventos), se utilizan tokens JWT.

### A. Iniciar Sesión (Obtener Token)
* **Endpoint:** `POST /api/auth/login/` o `POST /api/login/`
* **Body (JSON):**
```json
{
  "username": "carlos_turista",
  "password": "Pass1234!"
}
```
* **Respuesta Exitosa (200 OK):**
```json
{
  "message": "Inicio de sesión exitoso.",
  "user": {
    "id": 2,
    "username": "carlos_turista",
    "email": "carlos@example.com",
    "es_protagonista": false,
    "es_turista": true
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
  }
}
```

### B. Enviar Token en peticiones protegidas
Agrega el token de acceso en los Encabezados (Headers) HTTP:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

### C. Autenticación con Google (Google Sign-In / OAuth2)

Permite que los usuarios inicien sesión o se registren automáticamente utilizando su cuenta de Google. Si el usuario no existe en la base de datos, se crea de forma automática con su nombre, apellido, correo electrónico y foto de perfil proveniente de Google.

* **Guía de configuración en la nube:** Consulta [GUIA_GOOGLE_CLOUD_CONSOLE.md](GUIA_GOOGLE_CLOUD_CONSOLE.md) para generar el `Client ID` y `Client Secret` en Google Cloud Console.

#### 1. Iniciar Sesión / Registro con Google (Frontend SPA o Móvil)
* **Endpoint:** `POST /api/auth/google/` o `POST /api/google/`
* **Body (JSON):**
```json
{
  "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}
```
*(Nota: También acepta `"id_token"` en lugar de `"credential"`, o un `"code"` de autorización OAuth2).*

* **Respuesta Exitosa (200 OK):**
```json
{
  "message": "Autenticación con Google exitosa.",
  "is_new_user": false,
  "user": {
    "id": 5,
    "username": "maria_gonzalez",
    "email": "maria.gonzalez@gmail.com",
    "first_name": "María",
    "last_name": "González",
    "foto_perfil": "http://localhost:8000/media/perfiles/google_avatar_5.jpg",
    "es_protagonista": false,
    "es_turista": true
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
  }
}
```

#### 2. Flujo de Redirección Navegador (Opcional)
* **Obtener URL de Consentimiento:** `GET /api/auth/google/url/`
* **Callback de Redirección:** `GET /api/auth/google/callback/?code=...`
*(Si se visita desde el navegador, redirige a `FRONTEND_URL/auth/callback?access=...&refresh=...`)*

#### 3. Ejemplo de Integración en React (Vite / Next.js)
```bash
npm install @react-oauth/google
```
```jsx
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

export function GoogleAuthButton() {
  const handleSuccess = async (credentialResponse) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/google/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: credentialResponse.credential }),
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        console.log('Bienvenido:', data.user.first_name);
      }
    } catch (error) {
      console.error('Error autenticando con Google:', error);
    }
  };

  return (
    <GoogleOAuthProvider clientId="TU_GOOGLE_CLIENT_ID.apps.googleusercontent.com">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={() => console.error('Falló el inicio de sesión con Google')}
      />
    </GoogleOAuthProvider>
  );
}
```

---

## 3. Resumen de Endpoints Disponibles

| Recurso | Método HTTP | Endpoint | Descripción |
| :--- | :---: | :--- | :--- |
| **Google Auth (Token/Code)** | `POST` | `/api/auth/google/` | Iniciar sesión o registrarse con token o credencial de Google. |
| **Google Auth URL** | `GET` | `/api/auth/google/url/` | Obtener URL de consentimiento para redirección OAuth2. |
| **Google Callback** | `GET` | `/api/auth/google/callback/` | Callback para canjear código de autorización OAuth2. |
| **Ciudades** | `GET` | `/api/ciudades/` | Lista las 10 Ciudades Creativas con datos anidados. |
| **Detalle Ciudad** | `GET` | `/api/ciudades/{id}/` | Detalle completo de una ciudad por su ID. |
| **Circuitos Creativos**| `GET` | `/api/circuitos/` | Lista todos los circuitos creativos de las ciudades. |
| **Puntos de Interés** | `GET` | `/api/puntos-interes/` | Puntos de mapa con coordenadas GPS. |
| **Datos Históricos** | `GET` | `/api/datos-historicos/` | Mitos, leyendas, hitos históricos y saberes populares. |
| **Galería Multimedia**| `GET` | `/api/galeria-multimedia/` | Fotos y enlaces a vídeos inmersivos. |
| **Registrar Visita** | `POST` | `/api/visitas/` | Guarda la visita a un punto de interés del usuario autenticado. |
| **Obtener Visitas** | `GET` | `/api/visitas/` | Obtiene los datos completos de visitas del usuario autenticado. |
| **Obtener IDs Visitados** | `GET` | `/api/visitas/ids/` | Retorna únicamente los IDs de los puntos visitados `[1, 2, 5]`. |
| **Empresas / Destinos** | `GET` / `POST` | `/api/empresas/` | Empresas y destinos turísticos de usuarios protagonistas. |
| **Oportunidades Inversión**| `GET` / `POST` | `/api/oportunidades-inversion/` | Oportunidades de inversión publicadas por empresas. |
| **Inversiones Turistas** | `GET` / `POST` | `/api/inversiones-turistas/` | Formularios y ofertas de inversión enviadas por turistas. |
| **Eventos** | `GET` / `POST` | `/api/eventos/` | Agenda de actividades, talleres y ferias artesanales. |
| **Grano de Café (Evento)** | `POST` | `/api/eventos/{id}/grano-cafe/` | Alternar reacción de grano de café en un evento. |
| **Asistir a Evento** | `POST` | `/api/eventos/{id}/asistir/` | Confirmar o cancelar asistencia a un evento. |
| **Publicaciones** | `GET` / `POST` | `/api/publicaciones/` | Publicaciones y fotos de turistas y empresas/protagonistas. |
| **Like en Publicación** | `POST` | `/api/publicaciones/{id}/like/` | Alternar me gusta en una publicación. |
| **Comentarios de Publicación** | `GET` / `POST` | `/api/publicaciones/{id}/comentarios/` | Listar y agregar comentarios a una publicación. |
| **Comentarios Global** | `GET` / `POST` | `/api/comentarios-publicaciones/` | Endpoint CRUD para comentarios (filtro `?publicacion={id}`). |
| **Editar / Eliminar Comentario** | `PUT` / `PATCH` / `DELETE` | `/api/comentarios-publicaciones/{id}/` | Modificar o eliminar un comentario (solo el autor o staff). |

---

## 4. Estructura de Respuesta JSON (Ejemplo: `GET /api/ciudades/`)

Al consumir el endpoint de ciudades, la respuesta incluye automáticamente toda la información anidada para pintar en el mapa y la interfaz:

```json
[
  {
    "id": 1,
    "nombre": "León",
    "descripcion": "Ciudad universitaria y capital cultural, cuna de poetas y arquitectura colonial.",
    "imagen_portada": null,
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
        "imagen_mapa": null,
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
            "galeria": []
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
        "imagen": null,
        "video_url": null
      },
      {
        "id": 2,
        "ciudad": 1,
        "punto_interes": null,
        "titulo": "Documental: León, Cuna de la Revolución y Poesía",
        "tipo": "Video",
        "imagen": null,
        "video_url": "https://www.youtube.com/watch?v=ejemplo_leon_creativo"
      }
    ]
  }
]
```

---

## 5. Ejemplos de Código para Conectarse

### A. JavaScript (Fetch API / Async await - Web o React)

```javascript
// Obtener la lista de las 10 Ciudades Creativas con sus datos
async function obtenerCiudadesCreativas() {
  try {
    const response = await fetch('http://localhost:8000/api/ciudades/');
    if (!response.ok) {
      throw new Error(`Error HTTP: ${response.status}`);
    }
    const ciudades = await response.json();
    
    ciudades.forEach(ciudad => {
      console.log(`Ciudad: ${ciudad.nombre}`);
      console.log(`Circuitos: ${ciudad.circuitos.length}`);
      console.log(`Historias/Leyendas: ${ciudad.datos_historicos.length}`);
    });

    return ciudades;
  } catch (error) {
    console.error("Error conectando a la API de ciudades:", error);
  }
}

// Ejecutar
obtenerCiudadesCreativas();
```

---

### B. cURL (Línea de Comandos / Terminal)

```bash
# Consultar todas las ciudades
curl -X GET http://localhost:8000/api/ciudades/ -H "Accept: application/json"

# Consultar sólo los circuitos de Masaya o León
curl -X GET http://localhost:8000/api/circuitos/

# Consultar las leyendas e historias
curl -X GET http://localhost:8000/api/datos-historicos/
```

---

### C. Python (Librería `requests`)

```python
import requests

API_URL = "http://localhost:8000/api/ciudades/"

def cargar_ciudades():
    response = requests.get(API_URL)
    if response.status_code == 200:
        ciudades = response.json()
        print(f"Total de Ciudades obtenidas: {len(ciudades)}")
        for c in ciudades:
            print(f"- {c['nombre']}: {len(c['circuitos'])} circuitos, {len(c['datos_historicos'])} leyendas/datos.")
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    cargar_ciudades()
```

---

### D. Dart / Flutter (Aplicaciones Móviles iOS/Android)

```dart
import 'dart0:convert';
import 'http/http.dart' as http;

Future<void> fetchCiudades() async {
  final url = Uri.parse('http://10.0.2.2:8000/api/ciudades/'); // 10.0.2.2 para emulador Android
  final response = await http.get(url);

  if (response.statusCode == 200) {
    List<dynamic> ciudades = jsonDecode(response.body);
    print("Ciudades descargadas: ${ciudades.length}");
  } else {
    print("Error cargando ciudades: ${response.statusCode}");
  }
}
```

---

## 6. Registrar y Obtener Puntos Visitados (`usuario_puntos_visitados`)

Los siguientes ejemplos muestran cómo usar la API con la tabla `usuario_puntos_visitados` y validación de geolocalización GPS:

### A. Registrar Punto Visitado con Validación GPS (`POST /api/visitas/`)
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Body con GPS (Recomendado):**
```json
{
  "punto_interes_id": 1,
  "latitud_usuario": 12.4351,
  "longitud_usuario": -86.8789
}
```
* **Respuesta Exitosa (201 Created):**
El backend calcula la distancia usando la fórmula de Haversine. Si está a menos de 200 metros, asigna automáticamente `"es_validada": true`.
```json
{
  "id": 1,
  "usuario": 2,
  "usuario_id": 2,
  "punto_interes": 1,
  "punto_interes_id": 1,
  "punto_interes_nombre": "Insigne y Real Basílica Catedral de León",
  "circuito_nombre": "Ruta de los Poetas y Murales Históricos",
  "ciudad_nombre": "León",
  "fecha_visita": "2026-08-08T01:10:00Z",
  "latitud_usuario": 12.4351,
  "longitud_usuario": -86.8789,
  "es_validada": true,
  "distancia_metros": 15.42
}
```

### B. Obtener IDs de Puntos Visitados (`GET /api/visitas/ids/`)
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Respuesta Exitosa (200 OK):**
```json
[1, 3, 7]
```

---

## 7. Gestión de Empresas y Destinos Turísticos (`/api/empresas/`)

Permite a los usuarios protagonistas (`es_protagonista: true`) registrar la información de su empresa o destino turístico, especificando si aceptan inversión.

### A. Registrar Empresa / Destino (`POST /api/empresas/`)
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Body (JSON):**
```json
{
  "nombre": "Artesanías Monimbó",
  "descripcion": "Taller artesanal especializado en la confección de hamacas y cerámica tradicional.",
  "categoria": "Taller",
  "ciudad": 5,
  "direccion": "Barrio Monimbó, contiguo a la Plaza de San Jerónimo",
  "telefono_contacto": "+50588888888",
  "email_contacto": "contacto@artesaniasmonimbo.com",
  "sitio_web": "https://artesaniasmonimbo.com",
  "latitud": 11.9744,
  "longitud": -86.0942,
  "acepta_inversiones": true
}
```
* **Respuesta Exitosa (201 Created):**
```json
{
  "id": 1,
  "usuario": 3,
  "usuario_username": "protagonista_monimbo",
  "ciudad": 5,
  "ciudad_nombre": "Masaya",
  "punto_interes": null,
  "punto_interes_nombre": null,
  "nombre": "Artesanías Monimbó",
  "descripcion": "Taller artesanal especializado en la confección...",
  "categoria": "Taller",
  "direccion": "Barrio Monimbó, contiguo a la Plaza de San Jerónimo",
  "telefono_contacto": "+50588888888",
  "email_contacto": "contacto@artesaniasmonimbo.com",
  "sitio_web": "https://artesaniasmonimbo.com",
  "imagen_portada": null,
  "latitud": 11.9744,
  "longitud": -86.0942,
  "acepta_inversiones": true,
  "fecha_creacion": "2026-08-08T01:30:00Z"
}
```

### B. Listar Empresas (`GET /api/empresas/`)
* **Público.** Soporta filtros opcionales por parámetro query:
  * `GET /api/empresas/?acepta_inversiones=true`: Filtra solo las empresas abiertas a recibir inversiones.
  * `GET /api/empresas/?ciudad=5`: Filtra empresas por ID de Ciudad Creativa.

---

## 8. Módulo de Inversiones (`/api/oportunidades-inversion/` y `/api/inversiones-turistas/`)

Conecta a empresas que aceptan inversión (`acepta_inversiones: true`) con turistas nacionales o extranjeros interesados en invertir.

### A. Publicar Oportunidad de Inversión (`POST /api/oportunidades-inversion/`)
* **Headers:** `Authorization: Bearer <JWT_TOKEN>` *(El usuario debe ser propietario de la empresa)*.
* **Body (JSON):**
```json
{
  "empresa": 1,
  "titulo": "Ampliación de Taller para Exportación de Hamacas",
  "descripcion": "Buscamos capital para adquirir maquinaria de tejido y habilitar canal de exportación directo a Europa.",
  "monto_requerido": "5000.00",
  "monto_minimo_inversion": "100.00",
  "retorno_estimado": "15% de rendimiento anual",
  "tipo_inversor_permitido": "Todos"
}
```
* *Nota:* Si la empresa asociada tiene `"acepta_inversiones": false`, la API responderá con un error `400 Bad Request`.

### B. Registrar Inversión de Turista (`POST /api/inversiones-turistas/`)
Permite a un turista (nacional o extranjero) llenar el formulario de inversión.
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Body (JSON):**
```json
{
  "oportunidad": 1,
  "monto_propuesto": "500.00",
  "tipo_inversor": "Extranjero",
  "mensaje": "Me apasiona el arte nicaragüense y deseo invertir para impulsar este taller en Masaya.",
  "telefono_inversor": "+13055550199",
  "email_inversor": "inversor.extranjero@example.com"
}
```
* **Respuesta Exitosa (201 Created):**
```json
{
  "id": 1,
  "inversionista": 4,
  "inversionista_username": "john_tourist",
  "oportunidad": 1,
  "oportunidad_titulo": "Ampliación de Taller para Exportación de Hamacas",
  "empresa_id": 1,
  "empresa_nombre": "Artesanías Monimbó",
  "monto_propuesto": "500.00",
  "tipo_inversor": "Extranjero",
  "mensaje": "Me apasiona el arte nicaragüense...",
  "telefono_inversor": "+13055550199",
  "email_inversor": "inversor.extranjero@example.com",
  "estado": "Pendiente",
  "fecha_solicitud": "2026-08-08T01:32:00Z"
}
```

---

## 9. Agenda de Eventos y Mural de Publicación (`/api/eventos/`)

Permite tanto a usuarios **protagonistas** como a **administradores** publicar festividades, ferias artesanales, exposiciones y eventos oficiales de las Ciudades Creativas. Cada evento cuenta con un cálculo de visibilidad para el **mural de publicación**, activándose automáticamente una cantidad configurable de días (`dias_previos_mural`) antes de su inicio.

### A. Crear Evento (`POST /api/eventos/`)
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Body (JSON):**
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
  "cupo_maximo": 500
}
```
* **Respuesta Exitosa (201 Created / 200 OK):**
```json
{
  "id": 1,
  "creador": 1,
  "creador_username": "admin_alcaldia",
  "empresa": null,
  "empresa_nombre": null,
  "ciudad": 5,
  "ciudad_nombre": "Masaya",
  "titulo": "Feria Regional del Café y Artesanías",
  "descripcion": "Celebración oficial de la ciudad con degustación y talleres...",
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
  "user_ha_dado_grano_cafe": true,
  "total_asistentes": 42,
  "user_va_a_asistir": false,
  "galeria": [
    {
      "id": 5,
      "ciudad": null,
      "punto_interes": null,
      "evento": 1,
      "titulo": "Carrusel Detalle Evento 1",
      "tipo": "Imagen",
      "imagen": "/media/galeria/imagenes/feria1.jpg",
      "video_url": null
    }
  ],
  "publicaciones": [],
  "fecha_creacion": "2026-08-08T08:18:00Z"
}
```

### B. Consultar Eventos en el Mural (`GET /api/eventos/`)
* **Público.** Soporta filtrados por parámetro query:
  * `GET /api/eventos/?en_mural=true`: Retorna únicamente los eventos que están dentro de su ventana previa de publicación para el mural de la ciudad.
  * `GET /api/eventos/?es_oficial=true`: Filtra eventos oficiales creados por administradores.
  * `GET /api/eventos/?ciudad=5`: Filtra eventos por Ciudad Creativa.

### C. Reaccionar con Grano de Café en un Evento (`POST /api/eventos/{id}/grano-cafe/`)
Permite al usuario autenticado alternar (dar/quitar) su reacción de **Grano de Café** (icono de café en lugar de me gusta).
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Respuesta Exitosa (200 OK):**
```json
{
  "message": "Reacción de grano de café agregada al evento.",
  "ha_dado_grano_cafe": true,
  "total_granos_cafe": 154
}
```

### D. Confirmar Asistencia a un Evento (`POST /api/eventos/{id}/asistir/`)
Permite al usuario autenticado registrar o cancelar su intención de **asistir** al evento (`EventoAsistencia`).
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

## 10. Módulo de Publicaciones de Turistas y Protagonistas (`/api/publicaciones/`)

Permite a los turistas y a los protagonistas/empresas publicar contenido con imágenes, videos y descripciones. Las publicaciones pueden estar vinculadas opcionalmente a un evento, ciudad o empresa.

### A. Crear Publicación con Múltiples Imágenes (`POST /api/publicaciones/`)
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Content-Type:** `multipart/form-data`
* **Campos del Body:**
  * `descripcion`: Texto descriptivo de la publicación (Requerido).
  * `ciudad`: ID de la Ciudad Creativa (opcional).
  * `empresa`: ID de la Empresa / Destino (opcional).
  * `evento`: ID del Evento (opcional).
  * `imagen_principal`: Archivo de imagen de portada (opcional).
  * `imagenes`: Múltiples archivos de imagen para la galería/álbum de la publicación (hasta 10 fotos por petición).
  * `video_url`: URL de video (opcional).
  * `esta_activa`: `true` (opcional, por defecto `true`).

#### Ejemplo en React Native (JavaScript):
```javascript
async function crearPublicacionConFotos(token, descripcion, ciudadId, photosArray) {
  const formData = new FormData();
  formData.append('descripcion', descripcion);
  if (ciudadId) formData.append('ciudad', ciudadId);
  formData.append('esta_activa', 'true');

  // Adjuntar cada foto seleccionada en la clave de lista 'imagenes'
  photosArray.forEach((photo, index) => {
    formData.append('imagenes', {
      uri: photo.uri,
      type: photo.type || 'image/jpeg',
      name: photo.fileName || `foto_${index + 1}.jpg`,
    });
  });

  const response = await fetch('http://TU_SERVIDOR/api/publicaciones/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      // Importante: No definir 'Content-Type', fetch lo configura automáticamente con el boundary multipart
    },
    body: formData,
  });

  return await response.json();
}
```

#### Ejemplo en Flutter / Dart:
```dart
import 'package:http/http.dart' as http;

Future<void> publicarConFotos(String token, String descripcion, int ciudadId, List<String> photoPaths) async {
  var request = http.MultipartRequest(
    'POST',
    Uri.parse('http://TU_SERVIDOR/api/publicaciones/'),
  );

  request.headers['Authorization'] = 'Bearer $token';
  request.fields['descripcion'] = descripcion;
  request.fields['ciudad'] = ciudadId.toString();
  request.fields['esta_activa'] = 'true';

  // Adjuntar múltiples archivos en la clave 'imagenes'
  for (var path in photoPaths) {
    request.files.add(
      await http.MultipartFile.fromPath('imagenes', path),
    );
  }

  var streamedResponse = await request.send();
  var response = await http.Response.fromStream(streamedResponse);

  if (response.statusCode == 201) {
    print('Publicación creada con exito: ${response.body}');
  } else {
    print('Error al publicar: ${response.statusCode}');
  }
}
```

#### Ejemplo en cURL (Línea de Comandos):
```bash
curl -X POST http://localhost:8000/api/publicaciones/ \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -F "descripcion=Recorriendo los murales de Estelí con mis amigos" \
  -F "ciudad=1" \
  -F "esta_activa=true" \
  -F "imagenes=@/ruta/a/foto1.jpg" \
  -F "imagenes=@/ruta/a/foto2.jpg" \
  -F "imagenes=@/ruta/a/foto3.jpg"
```

* **Respuesta Exitosa (201 Created):**
```json
{
  "id": 1,
  "autor": 2,
  "autor_username": "carlos_turista",
  "autor_foto_perfil": "/media/perfiles/carlos.jpg",
  "es_protagonista": false,
  "empresa": null,
  "empresa_nombre": null,
  "ciudad": 1,
  "ciudad_nombre": "Estelí",
  "evento": 3,
  "evento_titulo": "Feria Regional del Café",
  "titulo": null,
  "descripcion": "Una experiencia increíble en la feria del café de Estelí.",
  "imagen_principal": null,
  "video_url": null,
  "imagenes": [
    {
      "id": 1,
      "imagen": "/media/publicaciones/colecciones/foto1.jpg",
      "fecha_creacion": "2026-08-15T09:30:00Z"
    },
    {
      "id": 2,
      "imagen": "/media/publicaciones/colecciones/foto2.jpg",
      "fecha_creacion": "2026-08-15T09:30:01Z"
    }
  ],
  "total_likes": 0,
  "user_ha_dado_like": false,
  "total_comentarios": 1,
  "comentarios": [
    {
      "id": 1,
      "publicacion": 1,
      "autor": 2,
      "autor_username": "carlos_turista",
      "autor_foto_perfil": "/media/perfiles/carlos.jpg",
      "contenido": "¡Excelente recomendación y hermosas fotos!",
      "esta_activo": true,
      "fecha_creacion": "2026-08-15T09:35:00Z"
    }
  ],
  "esta_activa": true,
  "fecha_creacion": "2026-08-15T09:30:00Z"
}
```

### B. Listar Publicaciones / Feed (`GET /api/publicaciones/`)
* **Público.** Filtros por parámetros de consulta (query params):
  * `GET /api/publicaciones/?evento=3`: Muestra las publicaciones asociadas a un evento específico.
  * `GET /api/publicaciones/?ciudad=1`: Muestra publicaciones de una ciudad.
  * `GET /api/publicaciones/?empresa=5`: Muestra publicaciones creadas por/para una empresa.
  * `GET /api/publicaciones/?autor=2`: Muestra publicaciones de un usuario en específico.

### C. Dar / Quitar Like a una Publicación (`POST /api/publicaciones/{id}/like/`)
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Respuesta Exitosa (200 OK):**
```json
{
  "message": "Like agregado a la publicación.",
  "ha_dado_like": true,
  "total_likes": 1
}
```

### D. Sistema de Comentarios en Publicaciones

#### 1. Listar Comentarios de una Publicación
* **Endpoints:** `GET /api/publicaciones/{id}/comentarios/` o `GET /api/comentarios-publicaciones/?publicacion={id}`
* **Acceso:** Público (no requiere autenticación).
* **Respuesta Exitosa (200 OK):**
```json
[
  {
    "id": 1,
    "publicacion": 1,
    "autor": 2,
    "autor_username": "carlos_turista",
    "autor_foto_perfil": "/media/perfiles/carlos.jpg",
    "contenido": "¡Excelente recomendación y hermosas fotos!",
    "esta_activo": true,
    "fecha_creacion": "2026-08-15T09:35:00Z"
  }
]
```

#### 2. Crear un Comentario en una Publicación
* **Endpoints:** `POST /api/publicaciones/{id}/comentarios/` o `POST /api/comentarios-publicaciones/`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Body (JSON):**
```json
{
  "contenido": "¡Increíble lugar, definitivamente lo visitaré!"
}
```
*(Nota: Si utilizas el endpoint `POST /api/comentarios-publicaciones/`, debes incluir `"publicacion": 1` en el JSON).*

* **Respuesta Exitosa (201 Created):**
```json
{
  "id": 2,
  "publicacion": 1,
  "autor": 3,
  "autor_username": "maria_protagonista",
  "autor_foto_perfil": "/media/perfiles/maria.jpg",
  "contenido": "¡Increíble lugar, definitivamente lo visitaré!",
  "esta_activo": true,
  "fecha_creacion": "2026-08-20T08:50:00Z"
}
```

#### 3. Editar un Comentario (PATCH / PUT)
* **Endpoint:** `PATCH /api/comentarios-publicaciones/{id}/` o `PUT /api/comentarios-publicaciones/{id}/`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>` *(Requerido: Debe ser el autor del comentario o usuario staff)*
* **Body (JSON):**
```json
{
  "contenido": "¡Increíble lugar, definitivamente lo visitaré! (Editado)"
}
```
* **Respuesta Exitosa (200 OK):** Retorna el comentario con el contenido actualizado.
* **Error de Permiso (403 Forbidden):** Retornado si un usuario intenta modificar el comentario de otra persona.

#### 4. Eliminar un Comentario (DELETE)
* **Endpoint:** `DELETE /api/comentarios-publicaciones/{id}/`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>` *(Requerido: Debe ser el autor del comentario o usuario staff)*
* **Respuesta Exitosa (204 No Content):** El comentario es eliminado y descontado del contador `total_comentarios` de la publicación.
* **Error de Permiso (403 Forbidden):** Retornado si un usuario intenta eliminar el comentario de otra persona.




