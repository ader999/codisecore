# 3. Resumen de Endpoints Disponibles

A continuación se presenta la tabla integral de endpoints de la API REST de **Ciudades Creativas**, organizada por módulos funcionales y niveles de acceso requeridos.

---

## 3.1 Módulos y Permisos

| Categoría | Método HTTP | Endpoint | Acceso Requerido | Descripción |
| :--- | :---: | :--- | :---: | :--- |
| **Autenticación** | `POST` | `/api/auth/login/` | Público | Autenticación con credenciales (usuario y contraseña) para obtener tokens JWT. |
| **Autenticación** | `POST` | `/api/auth/google/` | Público | Iniciar sesión o registrarse con token/credencial de Google OAuth2. |
| **Autenticación** | `GET` | `/api/auth/google/url/` | Público | Obtener la URL de consentimiento para flujo OAuth2 web. |
| **Autenticación** | `GET` | `/api/auth/google/callback/` | Público | Callback de redirección para canje de código OAuth2. |
| **Catálogo** | `GET` | `/api/ciudades/` | Público | Lista las 10 Ciudades Creativas con toda su estructura anidada. |
| **Catálogo** | `GET` | `/api/ciudades/{id}/` | Público | Detalle individual de una Ciudad Creativa. |
| **Catálogo** | `GET` | `/api/circuitos/` | Público | Listado de circuitos creativos turísticos. |
| **Catálogo** | `GET` | `/api/circuitos/{id}/empresas/` | Público | Lista empresas recomendadas (en ruta <= 800m y patrocinadas <= 5000m). |
| **Catálogo** | `GET` | `/api/puntos-interes/` | Público | Puntos de interés geolocalizados con coordenadas GPS. |
| **Catálogo** | `GET` | `/api/datos-historicos/` | Público | Mitos, leyendas, saberes y datos históricos. |
| **Catálogo** | `GET` | `/api/galeria-multimedia/`| Público | Fotografías y videos (incluyendo enlaces 360 / YouTube). |
| **Visitas GPS** | `POST` | `/api/visitas/` | Autenticado | Registrar la visita de un turista a un punto (valida Haversine < 200m). |
| **Visitas GPS** | `GET` | `/api/visitas/` | Autenticado | Listar historial completo de visitas del usuario autenticado. |
| **Visitas GPS** | `GET` | `/api/visitas/ids/` | Autenticado | Retorna array plano de IDs de puntos visitados (`[1, 2, 5]`). |
| **Empresas** | `GET` | `/api/empresas/` | Público | Directorio de empresas y destinos turísticos locales. |
| **Empresas** | `POST` | `/api/empresas/` | Protagonista | Registro de empresa/destino turístico por usuarios protagonistas. |
| **Multi-Empresa**| `GET` | `/api/empresas/mis_empresas/` | Autenticado | Listar empresas a las que pertenece el usuario (con su rol para switch de perfil). |
| **Multi-Empresa**| `GET` | `/api/empresas/{id}/miembros/` | Autenticado | Listar el equipo de miembros y roles de una empresa. |
| **Multi-Empresa**| `POST` | `/api/empresas/{id}/miembros/` | Owner / Admin | Invitar a un colaborador o actualizar su rol (OWNER, ADMIN, EDITOR). |
| **Inversiones** | `GET` | `/api/oportunidades-inversion/`| Público | Consultar oportunidades de inversión activas. |
| **Inversiones** | `POST` | `/api/oportunidades-inversion/`| Protagonista | Publicar oportunidad de inversión asociada a su empresa. |
| **Inversiones** | `GET` | `/api/inversiones-turistas/` | Autenticado | Listar solicitudes de inversión (filtrado por rol). |
| **Inversiones** | `POST` | `/api/inversiones-turistas/` | Turista | Postulación de oferta/intención de inversión de un turista. |
| **Eventos** | `GET` | `/api/eventos/` | Público | Agenda cultural y eventos (filtros `?en_mural=true`, `?ciudad=`). |
| **Eventos** | `POST` | `/api/eventos/` | Protagonista/Admin | Publicación de festividad, taller o feria cultural. |
| **Eventos** | `POST` | `/api/eventos/{id}/grano-cafe/` | Autenticado | Alternar (toggle) reacción de Grano de Café en el evento. |
| **Eventos** | `POST` | `/api/eventos/{id}/asistir/` | Autenticado | Confirmar o cancelar intención de asistencia al evento. |
| **Publicaciones** | `GET` | `/api/publicaciones/` | Público | Feed social de fotos de turistas y protagonistas. |
| **Publicaciones** | `POST` | `/api/publicaciones/` | Autenticado | Crear publicación con soporte multipart de hasta 10 fotos. |
| **Publicaciones** | `POST` | `/api/publicaciones/{id}/like/` | Autenticado | Alternar (toggle) Like a una publicación. |
| **Comentarios** | `GET` | `/api/publicaciones/{id}/comentarios/` | Público | Listar comentarios aprobados de una publicación. |
| **Comentarios** | `POST` | `/api/publicaciones/{id}/comentarios/` | Autenticado | Agregar un nuevo comentario a la publicación. |
| **Comentarios** | `PATCH` / `PUT`| `/api/comentarios-publicaciones/{id}/` | Autor/Staff | Modificar el contenido de un comentario propio. |
| **Comentarios** | `DELETE`| `/api/comentarios-publicaciones/{id}/` | Autor/Staff | Eliminar un comentario (descuenta del total de la publicación). |
| **Asistente IA**| `POST` | `/api/asistente/chat/` | Libre / Opcional | Chatbot con Google Gemini y Function Calling en tiempo real. |
| **Diagnóstico** | `GET` | `/api/health/` | Público | Healthcheck del sistema, base de datos y memoria. |

---

[⬅ Autenticación](02-autenticacion-jwt-google.md) | [Volver al Índice](README.md) | [Siguiente: Catálogo Turístico ➡](04-catalogo-turistico.md)
