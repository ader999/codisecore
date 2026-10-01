# Guía de Conexión a la API: Ciudades Creativas de Nicaragua

> 📌 **Aviso de Organización de Documentación:**  
> Debido a la extensión y profundidad técnica de esta guía, la documentación ha sido organizada y dividida en una estructura modular dentro de la carpeta [**`docs/api/`**](docs/api/README.md).

---

## 🚀 Acceso Rápido a los Módulos de la API

| Módulo | Enlace Directo | Descripción |
| :--- | :--- | :--- |
| **01. Configuración Base** | [**`docs/api/01-configuracion-base.md`**](docs/api/01-configuracion-base.md) | URLs base, límites Nginx/Django (50MB / 10 fotos) y soporte multi-idioma (ES, EN, ZH). |
| **02. Autenticación** | [**`docs/api/02-autenticacion-jwt-google.md`**](docs/api/02-autenticacion-jwt-google.md) | Tokens JWT, login, cabeceras `Authorization` y Google Sign-In OAuth2 con ejemplo en React. |
| **03. Resumen de Endpoints** | [**`docs/api/03-resumen-endpoints.md`**](docs/api/03-resumen-endpoints.md) | Matriz completa de endpoints, métodos HTTP, permisos requeridos y descripciones. |
| **04. Catálogo Turístico** | [**`docs/api/04-catalogo-turistico.md`**](docs/api/04-catalogo-turistico.md) | Ciudades, circuitos, puntos de interés, leyendas, galerías y estructura JSON anidada. |
| **05. Visitas y GPS** | [**`docs/api/05-visitas-geolocalizacion.md`**](docs/api/05-visitas-geolocalizacion.md) | Validación con fórmula Haversine (200m) y consulta ligera de IDs visitados (`/api/visitas/ids/`). |
| **06. Empresas y Multi-Empresa** | [**`docs/api/06-empresas-destinos.md`**](docs/api/06-empresas-destinos.md) | Membresías (`EmpresaMiembro`), roles (`OWNER`, `ADMIN`, `EDITOR`), switch de perfil (`mis_empresas`), gestión de equipo y cabecera `X-Company-Id`. |
| **07. Módulo de Inversiones** | [**`docs/api/07-modulo-inversiones.md`**](docs/api/07-modulo-inversiones.md) | Oportunidades de inversión publicadas por talleres y solicitudes/ofertas de turistas. |
| **08. Eventos y Mural** | [**`docs/api/08-agenda-eventos.md`**](docs/api/08-agenda-eventos.md) | Agenda cultural, cálculo automático para el mural, reacción Grano de Café y asistencia. |
| **09. Publicaciones Social** | [**`docs/api/09-publicaciones-comentarios.md`**](docs/api/09-publicaciones-comentarios.md) | Feed comunitario, subida de hasta 10 fotos (React Native/Flutter/cURL), Likes y comentarios CRUD. |
| **10. Asistente Virtual IA** | [**`docs/api/10-asistente-ia-eduardo.md`**](docs/api/10-asistente-ia-eduardo.md) | Asistente inteligente "Eduardo" (Gemini + Function Calling), GPS y código Kotlin Android nativo. |
| **11. Ejemplos de Clientes** | [**`docs/api/11-ejemplos-integracion-clientes.md`**](docs/api/11-ejemplos-integracion-clientes.md) | Plantillas de conexión listas en JavaScript, Dart/Flutter, Python y cURL. |

---

## 📖 Hub Central de Documentación

Para consultar los demás manuales técnicos del proyecto (Diagramas UML/ER, Guía de Producción, Seguridad y Buenas Prácticas), visita:

👉 [**Centro de Documentación del Proyecto (`docs/README.md`)**](docs/README.md)
