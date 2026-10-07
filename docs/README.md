# Centro de Documentación Técnica: CodiseCore

Bienvenido al centro oficial de documentación del backend **CodiseCore** (Plataforma y API REST de las **Ciudades Creativas de Nicaragua**).

Esta carpeta organiza y estructura de forma modular los manuales técnicos, guías de integración de API, playbooks de despliegue, políticas de seguridad y diagramas de arquitectura del sistema.

---

## 📚 Índice de Secciones

### 1. [Documentación de la API REST (`api/`)](api/README.md)
Guía técnica completa y modular para desarrolladores Frontend y Móviles (Android Nativo / Kotlin, Flutter / Dart, React):
* [**01. Configuración Base**](api/01-configuracion-base.md): URLs base, límites de subida de archivos (50MB / 10 fotos) y soporte multi-idioma (ES, EN, ZH).
* [**02. Autenticación (JWT y Google)**](api/02-autenticacion-jwt-google.md): Flujo de tokens JWT, Google Sign-In OAuth2 y ejemplo en React.
* [**03. Resumen de Endpoints**](api/03-resumen-endpoints.md): Matriz completa de endpoints, métodos y permisos requeridos.
* [**04. Catálogo Turístico**](api/04-catalogo-turistico.md): Ciudades, Circuitos, Puntos de Interés, Leyendas y Galerías (con JSON anidado).
* [**05. Visitas y Geolocalización GPS**](api/05-visitas-geolocalizacion.md): Validación geográfica con Haversine (200m) e IDs visitados.
* [**06. Empresas, Destinos y Multi-Empresa**](api/06-empresas-destinos.md): Membresías colaborativas (`EmpresaMiembro`), roles (`OWNER`, `ADMIN`, `EDITOR`), switch de perfil (`mis_empresas`), gestión de equipo y cabecera contextual `X-Company-Id`.
* [**07. Módulo de Inversiones**](api/07-modulo-inversiones.md): Publicación de rondas de inversión y postulación de turistas.
* [**08. Agenda de Eventos y Mural**](api/08-agenda-eventos.md): Mural automático, reacción con Grano de Café y confirmación de asistencia.
* [**09. Publicaciones y Comentarios**](api/09-publicaciones-comentarios.md): Red social, subida masiva de fotos, Likes y CRUD de comentarios.
* [**10. Asistente IA "Eduardo"**](api/10-asistente-ia-eduardo.md): Google Gemini con Function Calling, GPS y código Kotlin Android.
* [**11. Ejemplos de Clientes**](api/11-ejemplos-integracion-clientes.md): Código de integración rápido para JS, Flutter, Python y cURL.

---

### 2. Arquitectura del Sistema y Modelado de Datos
* [**Diagramas de Arquitectura UML y Modelo E-R 3FN**](../DIAGRAMAS_ARQUITECTURA_UML_ER.md): Especificación formal de entidades en Tercera Forma Normal (3FN), diagramas de clases, casos de uso y actividades en formato Mermaid.
* [**Visor Interactivo de Diagramas**](../diagramas_visor.html): Aplicación web standalone para inspección visual de la arquitectura.

---

### 3. Operaciones, Despliegue e Infraestructura
* [**Guía de Despliegue en Producción**](../GUIA_DESPLIEGUE_PRODUCCION.md): Arquitectura de contenedores Docker, Nginx, Gunicorn, Railway, Render, VPS Linux, certificados SSL/TLS y copias de seguridad.
* [**Configuración en Google Cloud Console**](../GUIA_GOOGLE_CLOUD_CONSOLE.md): Pasos para configurar OAuth 2.0 Client IDs, pantallas de consentimiento y credenciales de Google Sign-In.

---

### 4. Seguridad, Gobernanza y Desarrollo
* [**Manual de Seguridad y Buenas Prácticas**](../SEGURIDAD_Y_BUENAS_PRACTICAS.md): Gestión de secretos, defensas contra ataques (SQLi, XSS, CSRF, DDoS), políticas de contraseñas y checklist de auditoría.
* [**Flujo de Trabajo en Git**](../GUIA_GIT_FLUJO_TRABAJO.md): Convenciones de ramas, Git Flow y políticas de commits.
* [**Guía de Bienvenida y Onboarding (Visión de Producto y Negocio)**](GUIA_ONBOARDING_NO_TECNICA.md): Todo lo que un nuevo integrante debe saber sobre la app sin tecnicismos (visión, actores, módulos y glosario).
* [**Contexto del Proyecto**](../CONTEXTO_PROYECTO.md): Alcance funcional y requerimientos del reto de Ciudades Creativas.
* [**Plan de Eliminación de Campo Tipo Galería**](../PLAN_ELIMINACION_CAMPO_TIPO_GALERIA.md): Registro histórico de migración y optimización del esquema de datos.

---

[⬅ Volver al README Principal del Proyecto](../README.md)
