# 9. Módulo de Publicaciones y Comentarios

Este módulo gestiona la red social interactiva entre turistas y protagonistas. Permite publicar vivencias, compartir álbumes fotográficos (hasta 10 fotos por publicación), dar me gusta e interactuar mediante un sistema jerárquico de comentarios moderados.

---

## 9.1 Crear Publicación con Múltiples Imágenes (`POST /api/publicaciones/`)

* **Endpoint:** `POST /api/publicaciones/`
* **Headers:** 
  * `Authorization: Bearer <JWT_TOKEN>`
  * `Content-Type: multipart/form-data` *(configurado automáticamente por el cliente)*
  * `X-Company-Id: <ID_EMPRESA>` *(Opcional: Si se envía, la publicación se realiza a nombre de la empresa como `tipo_autor: 'EMPRESA'` en lugar de usuario personal)*

### Autoría Dual: Publicar como Usuario vs. como Empresa
* **Modo Personal (Por defecto):** Si no envías `X-Company-Id`, la publicación se crea con `tipo_autor: 'USUARIO'`, mostrando tu avatar y nombre personal.
* **Modo Empresa:** Si envías `X-Company-Id: 1` (o indicas `empresa: 1` en el form-data siendo miembro autorizado), la publicación se asigna con `tipo_autor: 'EMPRESA'`. El feed mostrará el logotipo y nombre de la empresa, y cualquier miembro con rol `OWNER`, `ADMIN` o `EDITOR` podrá gestionar la publicación.

### Campos Disponibles (Form-Data)

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `descripcion` | `String` | **Sí** | Texto o reseña de la experiencia. |
| `ciudad` | `Integer` | No | ID de la Ciudad Creativa relacionada. |
| `empresa` | `Integer` | No | ID de la empresa o taller vinculado (o inferido vía `X-Company-Id`). |
| `evento` | `Integer` | No | ID del evento vinculado. |
| `imagen_principal`| `File` | No | Foto de portada de la publicación. |
| `imagenes` | `Files` | No | Lista de hasta 10 archivos de imagen para la galería/carrusel. |
| `video_url` | `String` | No | Enlace opcional a video de YouTube o red externa. |
| `esta_activa` | `Boolean` | No | Estado de visibilidad (por defecto `true`). |

---

### Ejemplos de Implementación para Clientes

#### Ejemplo en React Native (JavaScript)
```javascript
async function crearPublicacionConFotos(token, descripcion, ciudadId, photosArray) {
  const formData = new FormData();
  formData.append('descripcion', descripcion);
  if (ciudadId) formData.append('ciudad', ciudadId);
  formData.append('esta_activa', 'true');

  // Adjuntar cada foto seleccionada en la clave repetible 'imagenes'
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
      // No definir 'Content-Type': el motor de fetch asigna automáticamente el boundary multipart
    },
    body: formData,
  });

  return await response.json();
}
```

#### Ejemplo en Flutter / Dart
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

  // Adjuntar múltiples archivos a la clave 'imagenes'
  for (var path in photoPaths) {
    request.files.add(
      await http.MultipartFile.fromPath('imagenes', path),
    );
  }

  var streamedResponse = await request.send();
  var response = await http.Response.fromStream(streamedResponse);

  if (response.statusCode == 201) {
    print('Publicación creada con éxito: ${response.body}');
  } else {
    print('Error al publicar: ${response.statusCode}');
  }
}
```

#### Ejemplo en cURL
```bash
curl -X POST http://localhost:8000/api/publicaciones/ \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -F "descripcion=Recorriendo los murales de Estelí con amigos" \
  -F "ciudad=1" \
  -F "esta_activa=true" \
  -F "imagenes=@/ruta/a/foto1.jpg" \
  -F "imagenes=@/ruta/a/foto2.jpg" \
  -F "imagenes=@/ruta/a/foto3.jpg"
```

### Respuesta Exitosa (`201 Created`)
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

---

## 9.2 Listar Feed y Filtros (`GET /api/publicaciones/`)

Endpoint público para renderizar el feed de la comunidad con filtros de búsqueda:

```bash
# Feed general
GET /api/publicaciones/

# Publicaciones asociadas a un evento
GET /api/publicaciones/?evento=3

# Publicaciones de una Ciudad Creativa
GET /api/publicaciones/?ciudad=1

# Publicaciones de un negocio o taller específico
GET /api/publicaciones/?empresa=5

# Publicaciones de un usuario en particular
GET /api/publicaciones/?autor=2
```

---

## 9.3 Dar o Retirar Like (`POST /api/publicaciones/{id}/like/`)

* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Respuesta Exitosa (200 OK):**
```json
{
  "message": "Like agregado a la publicación.",
  "ha_dado_like": true,
  "total_likes": 1
}
```

---

## 9.4 Sistema Completo de Comentarios

### 1. Listar Comentarios de una Publicación
* **Endpoint:** `GET /api/publicaciones/{id}/comentarios/` *(o `GET /api/comentarios-publicaciones/?publicacion={id}`)*
* **Acceso:** Libre (no requiere autenticación).

### 2. Crear Comentario
* **Endpoint:** `POST /api/publicaciones/{id}/comentarios/`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Body (JSON):**
```json
{
  "contenido": "¡Increíble lugar, definitivamente lo visitaré!"
}
```
* **Respuesta Exitosa (`201 Created`):** Retorna el comentario con los datos de autor y marca de tiempo.

### 3. Editar Comentario
* **Endpoint:** `PATCH /api/comentarios-publicaciones/{id}/`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>` *(Requiere ser el autor del comentario o usuario staff)*
* **Body (JSON):**
```json
{
  "contenido": "¡Increíble lugar, definitivamente lo visitaré! (Editado)"
}
```

### 4. Eliminar Comentario
* **Endpoint:** `DELETE /api/comentarios-publicaciones/{id}/`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>` *(Requiere ser el autor o usuario staff)*
* **Respuesta Exitosa (`204 No Content`):** El comentario se elimina y se decrementa el contador `total_comentarios`.

---

[⬅ Agenda de Eventos y Mural](08-agenda-eventos.md) | [Volver al Índice](README.md) | [Siguiente: Asistente Virtual IA "Eduardo" ➡](10-asistente-ia-eduardo.md)
