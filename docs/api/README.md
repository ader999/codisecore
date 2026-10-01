# Guía de Conexión a la API REST: Ciudades Creativas de Nicaragua

Bienvenido a la documentación técnica modular de la API REST de **Ciudades Creativas de Nicaragua**. Esta guía está diseñada para desarrolladores de aplicaciones móviles (**Android nativo / Kotlin**, **Flutter / Dart**, **iOS / Swift**), aplicaciones web (**React**, **Next.js**, **Vue**) y servicios backend.

---

## 🗺️ Mapa de Contenidos

La documentación ha sido dividida en módulos temáticos específicos para facilitar su lectura y mantenimiento:

1. [**01. Configuración Base**](01-configuracion-base.md)
   * URLs base (Desarrollo, Emulador y Producción).
   * Límites de subida multipart (Nginx, Gunicorn y Django para hasta 10 fotos).
   * Localización multi-idioma (Español, Inglés y Chino Mandarín) vía cabeceras y parámetros.

2. [**02. Autenticación (JWT y Google OAuth2)**](02-autenticacion-jwt-google.md)
   * Inicio de sesión con credenciales (`/api/auth/login/`).
   * Envío del encabezado `Authorization: Bearer <token>`.
   * Integración de Google Sign-In (`/api/auth/google/`) con creación automática de usuario y ejemplo en React.

3. [**03. Resumen y Referencia de Endpoints**](03-resumen-endpoints.md)
   * Tabla completa de todos los endpoints, métodos HTTP, niveles de acceso y descripciones.

4. [**04. Catálogo Turístico**](04-catalogo-turistico.md)
   * Consulta de Ciudades Creativas, Circuitos y Puntos de Interés.
   * Historias, leyendas, mitos y galerías multimedia.
   * Estructura JSON anidada completa y consultas optimizadas para mapas.

5. [**05. Visitas y Geolocalización GPS**](05-visitas-geolocalizacion.md)
   * Validación geográfica con la fórmula Haversine (rango de 200m).
   * Registro de visitas verificadas (`/api/visitas/`).
   * Consulta ultra-rápida de IDs visitados (`/api/visitas/ids/`) para marcadores de mapa.

6. [**06. Gestión de Empresas, Destinos y Multi-Empresa**](06-empresas-destinos.md)
   * Arquitectura Multi-Empresa: relación usuario-empresa mediante membresías colaborativas (`EmpresaMiembro`).
   * Roles de equipo: Propietario (`OWNER`), Administrador (`ADMIN`) y Editor (`EDITOR`).
   * Selector de perfiles: endpoint `GET /api/empresas/mis_empresas/` para cambiar de rol en la app.
   * Gestión de colaboradores: endpoints `GET` y `POST /api/empresas/{id}/miembros/`.
   * Cambio de contexto dinámico: encabezado HTTP `X-Company-Id: <id>` para operar a nombre del negocio.
   * Registro y directorio público de empresas con filtros.

7. [**07. Módulo de Inversiones**](07-modulo-inversiones.md)
   * Publicación de oportunidades de inversión por emprendedores locales.
   * Formulario de postulación de ofertas de inversión por turistas nacionales o internacionales.

8. [**08. Agenda de Eventos y Mural de la Ciudad**](08-agenda-eventos.md)
   * Publicación de festividades, talleres y ferias culturales.
   * Sistema de cálculo automático para el mural de la ciudad (`?en_mural=true`).
   * Reacciones con Grano de Café e intención de asistencia.

9. [**09. Módulo de Publicaciones y Comentarios**](09-publicaciones-comentarios.md)
   * Feed comunitario y publicaciones con múltiples fotos (hasta 10 imágenes).
   * Ejemplos de subida multipart en React Native, Flutter y cURL.
   * Sistema de Likes y gestión CRUD completa de comentarios.

10. [**10. Asistente Virtual Turístico Inteligente "Eduardo" (Gemini AI)**](10-asistente-ia-eduardo.md)
    * Integración de Google Gemini con Function Calling (Tool Calling) en tiempo real.
    * Modelos `gemini-3.1-flash-lite` y fallback automático `gemini-3.8-flash`.
    * Búsqueda por proximidad GPS y soporte internacional (ES / EN / ZH).
    * Implementación completa en Android Nativo (Kotlin + Retrofit + Coroutines).

11. [**11. Ejemplos de Integración y Clientes**](11-ejemplos-integracion-clientes.md)
    * Plantillas listas para copiar y pegar en JavaScript (Fetch API), Dart/Flutter, Python y cURL.

---

[⬅ Volver al Hub Principal de Documentación](../README.md)
