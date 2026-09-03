<div align="center">

```
  ____   ___   ____   ___   ____  _____ _     _   _ 
 / ___| / _ \ |  _ \ |_ _| / ___|| ____| |   | | | |
| |    | | | || | | | | | | |    |  _| | |   | | | |
| |___ | |_| || |_| | | | | |___ | |___| |___| |_| |
 \____| \___/ |____/ |___| \____||_____|_____|\___/ 

      Backend API - Ciudades Creativas de Nicaragua
```

# Codice路

**API REST en Django para la Red Nacional de Ciudades Creativas y Turismo Cultural**

[![Python Version](https://img.shields.io/badge/python-v3.13-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-v6.0-green.svg)](https://www.djangoproject.com/)
[![DRF Version](https://img.shields.io/badge/DRF-v3.15-red.svg)](https://www.django-rest-framework.org/)
[![Docker Ready](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)]()

---

</div>

## Tabla de Contenidos

- [1. Descripcion General](#1-descripcion-general)
- [2. Arquitectura del Sistema](#2-arquitectura-del-sistema)
  - [2.1. Diagrama de Capas del Sistema](#21-diagrama-de-capas-del-sistema)
  - [2.2. Modelo de Datos y Relaciones](#22-modelo-de-datos-y-relaciones)
  - [2.3. Autenticacion y Control de Acceso](#23-autenticacion-y-control-de-acceso)
  - [2.4. Arquitectura de Almacenamiento y Streaming de Archivos](#24-arquitectura-de-almacenamiento-y-streaming-de-archivos)
  - [2.5. Algoritmo de Validacion Geografica (Haversine)](#25-algoritmo-de-validacion-geografica-haversine)
- [3. Estructura Modular del Proyecto](#3-estructura-modular-del-proyecto)
  - [3.1. Arbol de Directorios](#31-arbol-de-directorios)
  - [3.2. Responsabilidad de Modulos](#32-responsabilidad-de-modulos)
- [4. Dependencias y Tecnologias](#4-dependencias-y-tecnologias)
  - [4.1. Entorno de Ejecucion](#41-entorno-de-ejecucion)
  - [4.2. Dependencias de Python](#42-dependencias-de-python)
  - [4.3. Infraestructura y Servicios](#43-infraestructura-y-servicios)
- [5. Variables de Entorno](#5-variables-de-entorno)
  - [5.1. Matriz de Variables de Configuracion](#51-matriz-de-variables-de-configuracion)
  - [5.2. Archivo .env de Ejemplo](#52-archivo-env-de-ejemplo)
- [6. Scripts y Comandos de Administracion](#6-scripts-y-comandos-de-administracion)
  - [6.1. Despliegue con Docker y Docker Compose](#61-despliegue-con-docker-y-docker-compose)
  - [6.2. Ejecucion y Desarrollo Local](#62-ejecucion-y-desarrollo-local)
  - [6.3. Comandos de Mantenimiento de Django](#63-comandos-de-mantenimiento-de-django)
  - [6.4. Flujo de Inicializacion (entrypoint.sh)](#64-flujo-de-inicializacion-entrypointsh)
- [7. Catalogo y Ejemplos de Endpoints de la API](#7-catalogo-y-ejemplos-de-endpoints-de-la-api)
  - [7.1. Autenticacion y Usuarios](#71-autenticacion-y-usuarios)
  - [7.2. Ciudades y Circuitos Creativos](#72-ciudades-y-circuitos-creativos)
  - [7.3. Puntos de Interes y Datos Historicos](#73-puntos-de-interes-y-datos-historicos)
  - [7.4. Validacion de Visitas GPS](#74-validacion-de-visitas-gps)
  - [7.5. Empresas y Protagonistas](#75-empresas-y-protagonistas)
  - [7.6. Oportunidades e Inversiones Turisticas](#76-oportunidades-e-inversiones-turisticas)
  - [7.7. Eventos, Asistencias y Granos de Cafe](#77-eventos-asistencias-y-granos-de-cafe)
  - [7.8. Publicaciones, Galeria Masiva y Comentarios](#78-publicaciones-galeria-masiva-y-comentarios)
- [8. Contribucion](#8-contribucion)
- [9. Autores y Agradecimientos](#9-autores-y-agradecimientos)
- [10. Licencia](#10-licencia)

---

## 1. Descripcion General

Codice路 es un servicio backend desarrollado con Django y Django REST Framework disenado para centralizar, estructurar y exponer la oferta cultural, turistica, gastronomica y de emprendimiento de las Ciudades Creativas de Nicaragua:

1. Esteli
2. Leon
3. Nagarote
4. Managua
5. Masaya
6. Granada
7. San Juan de Oriente
8. Juigalpa
9. Matagalpa
10. Bluefields

La API atiende solicitudes desde clientes moviles nativos (Kotlin / Android), aplicaciones web y paneles de administracion, ofreciendo soporte para navegacion GIS, validacion de proximidad por coordenadas, registro de asistencia a eventos, catalogo de inversiones locales y un feed social con carga masiva de imagenes.

---

## 2. Arquitectura del Sistema

### 2.1. Diagrama de Capas del Sistema

```text
+-------------------------------------------------------------------------+
|                           CAPA DE CLIENTES                              |
|   App Movil Android (Kotlin)   |   Cliente Web   |   Panel Admin Django |
+------------------------------------+--------------------+---------------+
                                     |
                                     | HTTP / HTTPS (REST JSON & Multipart)
                                     v
+-------------------------------------------------------------------------+
|                     CAPA DE PROXY INVERSO (Nginx)                       |
|   - Manejo de client_max_body_size (50 MB)                              |
|   - Timeouts extendidos de subida (300s)                                |
|   - Servicio optimizado de archivos estaticos /static/ con WhiteNoise   |
+------------------------------------+------------------------------------+
                                     |
                                     | Proxy Pass (HTTP / Socket)
                                     v
+-------------------------------------------------------------------------+
|                  CAPA DE APLICACION WSGI (Gunicorn)                     |
|   - Workers sincronos / asincronos con timeout de 300s                  |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                     CAPA BACKEND (Django 6.0 + DRF)                     |
|   - Enrutamiento y Controladores (ViewSets & Generics)                  |
|   - Logica de Validacion y Serializacion (DRF Serializers)              |
|   - Autenticacion Stateless JWT (SimpleJWT)                             |
|   - Modulo de Calculo Espacial Haversine                                |
|   - Storage Engine Router (django-storages)                             |
+-------------------+--------------------------------+--------------------+
                    |                                |
                    v                                v
+------------------------------------+   +--------------------------------+
|    CAPA DE PERSISTENCIA RELACIONAL |   |    ALMACENAMIENTO DE OBJETOS   |
|   PostgreSQL / SQLite3             |   |   AWS S3 / Compatible Storage  |
|   - Entidades, Relaciones y GIS    |   |   - Imagenes de Publicaciones  |
|   - Indices y Restricciones        |   |   - Portadas y Galerias        |
+------------------------------------+   +--------------------------------+
```

---

### 2.2. Modelo de Datos y Relaciones

> 📘 **Documentación Técnica Completa:** Para consultar los diagramas formales en Tercera Forma Normal (3FN), el Diagrama de Clases UML, Casos de Uso y Diagramas de Actividades, consulta [DIAGRAMAS_ARQUITECTURA_UML_ER.md](DIAGRAMAS_ARQUITECTURA_UML_ER.md) o visualízalos interactivamente en [diagramas_visor.html](diagramas_visor.html).

El esquema relacional esta compuesto por 13 entidades principales organizadas para garantizar integridad referencial y alto rendimiento en consultas anidadas:

```text
[ Ciudad ] 1 ──── N [ CircuitoCreativo ] 1 ──── N [ PuntoInteres ] 1 ──── N [ DatoHistorico ]
    │                      │                             │
    │                      │                             ├────── N [ GaleriaMultimedia ]
    │                      │                             │
    │                      │                             └────── N [ UsuarioPuntoVisitado ]
    │                      │                                               │
    ├────── N [ Empresa ] ─┴───────────────────────────────────────────────┤ (FK Usuario)
    │           │                                                          │
    │           ├────── N [ OportunidadInversion ] 1 ──── N [ InversionTurista ]
    │           │
    │           └────── N [ Evento ] 1 ──── N [ EventoAsistencia ]
    │                       │
    │                       ├────── N [ User (M2M Granos de Cafe) ]
    │                       └────── N [ GaleriaMultimedia ]
    │
    └────── N [ Publicacion ] 1 ──── N [ PublicacionImagen ]
                │
                ├────── N [ ComentarioPublicacion ]
                └────── N [ User (M2M Likes) ]
```

#### Descripcion de Entidades del Modelo

| Entidad | Tabla / Modelo | Descripcion Tecnica |
| :--- | :--- | :--- |
| `User` | `codiselu.User` | Modelo de usuario extendido de `AbstractUser`. Contiene banderas `es_protagonista`, `es_turista`, `telefono` y `foto_perfil`. |
| `Ciudad` | `codiselu.Ciudad` | Nodo principal territorial. Almacena coordenadas centrales (`latitud_centro`, `longitud_centro`), descripcion y portada. |
| `CircuitoCreativo` | `codiselu.CircuitoCreativo` | Agrupador de rutas turisticas (`Baja`, `Media`, `Alta`), distancia en km y duracion estimada. |
| `PuntoInteres` | `codiselu.PuntoInteres` | Marcador geografico individual con orden secuencial, coordenadas GPS y categorizacion tematica. |
| `DatoHistorico` | `codiselu.DatoHistorico` | Registro cultural clasificado en `Hito`, `Leyenda`, `SaberPopular` o `Gastronomia`. Vinculado a Ciudad o Punto. |
| `GaleriaMultimedia` | `codiselu.GaleriaMultimedia` | Registro de elementos visuales (imagenes o URLs de video) vinculados a Ciudad, Punto o Evento. |
| `UsuarioPuntoVisitado`| `usuario_puntos_visitados` | Tabla de paso que almacena la traza GPS del turista, distancia calculada y bandera de validacion booleana. |
| `Empresa` | `codiselu.Empresa` | Perfil comercial de protagonistas locales. Incluye categoria, coordenadas y estado `acepta_inversiones`. |
| `OportunidadInversion`| `codiselu.OportunidadInversion` | Proyectos de recaudacion con montos minimos, objetivos y restricciones de tipo de inversor. |
| `InversionTurista` | `codiselu.InversionTurista` | Intencion formal de inversion registrada por un turista, con estados `Pendiente`, `Aprobada`, `Rechazada`. |
| `Evento` | `codiselu.Evento` | Actividades publicas y oficiales con control de aforo, bandera `en_mural` computada y sistema de Granos de Cafe. |
| `EventoAsistencia` | `codiselu.EventoAsistencia` | Registro de confirmacion de asistencia de usuarios a eventos. |
| `Publicacion` | `codiselu.Publicacion` | Elemento principal del feed social con imagen de portada, relacion M2M de likes y enlaces a entidades. |
| `PublicacionImagen` | `codiselu.PublicacionImagen` | Imagenes complementarias de una publicacion (soporte multi-imagen hasta 10 archivos). |
| `ComentarioPublicacion`| `codiselu.ComentarioPublicacion` | Hilos de discusion vinculados a publicaciones. |

---

### 2.3. Autenticacion y Control de Acceso

El sistema implementa autenticacion sin estado basada en JSON Web Tokens mediante `djangorestframework-simplejwt`:

- **Formato del encabezado de autorizacion**:
  ```http
  Authorization: Bearer <access_token>
  ```
- **Vigencia de Tokens**:
  - `Access Token`: 24 horas (1 dia).
  - `Refresh Token`: 7 dias.
- **Politicas de Permisos**:
  - `AllowAny`: Consulta publica de Ciudades, Circuitos, Puntos, Eventos, Publicaciones y Autenticacion.
  - `IsAuthenticated`: Registro de visitas GPS, inversion de turistas, interaccion con granos de cafe, likes y edicion de perfil.
  - `IsAuthenticatedOrReadOnly`: Permite lectura publica y restringe creacion/modificacion a usuarios autenticados.
  - `IsAutorOrReadOnly`: Restringe operaciones de actualizacion y borrado de comentarios exclusivamente al creador original o administradores (`is_staff`).
  - `IsAdminUser`: Operaciones directas de gestion de usuarios sobre `/api/users/`.

---

### 2.4. Arquitectura de Almacenamiento y Streaming de Archivos

Para soportar el envio masivo de fotografias de alta resolucion desde redes moviles con ancho de banda variable, la arquitectura distribuye los limites de la siguiente forma:

1. **Nginx Proxy (`nginx/default.conf`)**:
   - `client_max_body_size 50M;`: Permite cuerpos de peticion HTTP de hasta 50 Megabytes.
   - `client_body_buffer_size 10M;`: Mantiene en memoria buffers intermedios para transmisiones rapidas.
   - `client_body_timeout 300s;`, `proxy_read_timeout 300s;`: Evita el corte prematuro de sockets en subidas lentas.

2. **Django Core (`codiselu/settings.py`)**:
   - `DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800` (50 MB).
   - `FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400` (25 MB por archivo individual).
   - `DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000`.

3. **Almacenamiento Hibrido (`django-storages` + S3 / Local)**:
   - En modo S3 (`USE_S3=True`): Los archivos multimedia se transmiten directamente al bucket de Object Storage compatible con AWS S3 mediante `boto3`.
   - En modo local (`USE_S3=False`): Los archivos se guardan en el sistema de ficheros bajo el directorio `/app/media/`.

---

### 2.5. Algoritmo de Validacion Geografica (Haversine)

Cuando un cliente envia coordenadas GPS al registrar una visita en `/api/visitas/`, el backend ejecuta la formula del semiverseno (Haversine) para determinar la distancia geodesica real respecto a las coordenadas oficiales del `PuntoInteres`:

$$\Delta\sigma = 2 \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)} \right)$$

$$d = R \cdot \Delta\sigma$$

- $R = 6,371,000 \text{ metros}$ (Radio medio de la Tierra).
- **Criterio de Aceptacion**: Si la distancia calculada $d \le 200.0 \text{ metros}$, la visita se marca automaticamente como `es_validada = True`. En caso contrario, se registra con `es_validada = False` y se almacena la distancia calculada en `distancia_metros`.

---

## 3. Estructura Modular del Proyecto

### 3.1. Arbol de Directorios

```text
codisecore/
├── codiselu/                      # Paquete principal de la aplicacion Django
│   ├── __init__.py                # Inicializador del paquete Python
│   ├── asgi.py                    # Configuracion ASGI para servidores asincronos
│   ├── wsgi.py                    # Configuracion WSGI para Gunicorn
│   ├── settings.py                # Configuracion global, seguridad, DB, S3 y DRF
│   ├── urls.py                    # Enrutamiento de URLs, ViewSets y vistas de autenticacion
│   ├── models.py                  # Definicion de los 13 modelos de datos del sistema
│   ├── serializers.py             # Serializadores de DRF, validaciones y calculo Haversine
│   ├── views.py                   # ViewSets, Generics, APIs y logica de negocio
│   ├── admin.py                   # Configuracion del panel de administracion de Django
│   ├── apps.py                    # Configuracion de la aplicacion Django
│   └── migrations/                # Scripts de migracion de esquema de base de datos
├── nginx/                         # Configuracion del servidor Web / Reverse Proxy
│   └── default.conf               # Reglas de proxy reverso, timeouts y buffers
├── static/                        # Archivos estaticos fuente del proyecto
├── staticfiles/                   # Directorio destino de assets recolectados (collectstatic)
├── CONTEXTO_PROYECTO.md           # Documento de contexto del reto y alcance funcional
├── GUIA_CONEXION_API.md           # Guia de integracion para desarrolladores frontend/movil
├── Dockerfile                     # Construccion multi-stage de la imagen Docker de produccion
├── docker-compose.yml             # Orquestacion de servicios (web, nginx, volumenes)
├── entrypoint.sh                  # Script de inicio del contenedor (migraciones automaticas)
├── manage.py                      # Interfaz de linea de comandos de Django
├── pyproject.toml                 # Declaracion de dependencias y metadata del proyecto (PEP 621)
├── uv.lock                        # Bloqueo deterministico de dependencias
├── .env                           # Variables de entorno locales (no versionar credenciales reales)
├── .dockerignore                  # Reglas de exclusion para el contexto de construccion Docker
├── .gitignore                     # Reglas de exclusion para control de versiones Git
└── README.md                      # Documentacion tecnica principal del repositorio
```

---

### 3.2. Responsabilidad de Modulos

- **`codiselu/models.py`**:
  Contiene la definicion de las entidades de dominio y sus propiedades computadas (`en_mural`, `total_granos_cafe`, `total_asistentes`, `total_likes`, `total_comentarios`).
- **`codiselu/serializers.py`**:
  Gestiona la transformacion bidireccional entre instancias de modelos y representaciones JSON, aplicando validaciones de contraseñas, unicidad de correos, restricciones de inversion y resolucion de proximidad espacial.
- **`codiselu/views.py`**:
  Implementa la logica de respuesta HTTP, control de permisos (`IsAutorOrReadOnly`), filtros por parametros query y endpoints de accion (`toggle_like`, `grano_cafe`, `asistir`, `obtener_ids_visitados`, `comentarios`).
- **`codiselu/urls.py`**:
  Define la estructura de rutas mediante `DefaultRouter` de DRF y expone las rutas de autenticacion JWT bajo `/api/auth/`.
- **`nginx/default.conf`**:
  Actua como capa perimetral para aislar Gunicorn, servir estaticos con directivas de cache (`expires 30d`) y procesar cargas pesadas sin estrangular el servidor de aplicaciones.

---

## 4. Dependencias y Tecnologias

### 4.1. Entorno de Ejecucion

- **Python**: `>= 3.13`
- **Motor de Base de Datos**: PostgreSQL 15+ (Produccion) / SQLite3 (Desarrollo local)
- **Servidor Web / Proxy**: Nginx Alpine
- **Gestor de Procesos WSGI**: Gunicorn 23.0+
- **Gestor de Paquetes**: `uv` (Astral) o `pip`

---

### 4.2. Dependencias de Python

Las dependencias del proyecto se gestionan en `pyproject.toml`:

| Paquete | Version Minima | Proposito en el Sistema |
| :--- | :--- | :--- |
| `django` | `>= 6.0.6` | Framework web base del sistema. |
| `djangorestframework` | `>= 3.15.2` | Conjunto de herramientas para construir la API REST. |
| `djangorestframework-simplejwt` | `>= 5.5.0` | Autenticacion JSON Web Token (JWT). |
| `psycopg2-binary` | `*` | Adaptador de base de datos PostgreSQL para Python. |
| `django-storages[boto3]` | `>= 1.14` | Soporte de almacenamiento de archivos multimedia en AWS S3 y S3-compatibles. |
| `pillow` | `>= 12.3.0` | Procesamiento y validacion de formatos de imagen (`ImageField`). |
| `whitenoise` | `>= 6.0.0` | Servicio optimizado y compresion de archivos estaticos. |
| `gunicorn` | `>= 23.0.0` | Servidor HTTP WSGI para ejecucion en entornos de produccion. |
| `python-dotenv` | `>= 1.0.0` | Carga automatica de variables de entorno desde archivos `.env`. |

---

### 4.3. Infraestructura y Servicios

- **Docker**: Motor de virtualizacion de contenedores (`>= 20.10`).
- **Docker Compose**: Orquestador multi-contenedor (`>= 2.0`).
- **Object Storage**: AWS S3, Cloudflare R2, MinIO o Railway Storage API.

---

## 5. Variables de Entorno

### 5.1. Matriz de Variables de Configuracion

| Variable | Tipo | Obligatoria | Valor por Defecto | Descripcion Tecnica |
| :--- | :--- | :---: | :--- | :--- |
| `DJANGO_SECRET_KEY` | String | Si | `django-insecure-...` | Clave criptografica para firma de sesiones y tokens. |
| `DJANGO_DEBUG` | Booleano | No | `False` | Habilita o deshabilita el modo de depuracion de Django. |
| `DJANGO_ALLOWED_HOSTS` | String (CSV) | No | `*` | Dominios y direcciones IP autorizados para peticiones entrantes. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | String (CSV) | No | Lista predefinida | Origenes seguros para validacion de proteccion CSRF. |
| `DATABASE_URL` | String URI | No | None | URI de conexion PostgreSQL (`postgresql://user:pass@host:port/db`). |
| `DB_NAME` | String | No | `postgres` | Nombre de la base de datos PostgreSQL si no se usa `DATABASE_URL`. |
| `DB_USER` | String | No | `postgres` | Usuario de conexion PostgreSQL. |
| `DB_PASSWORD` | String | No | `""` | Contraseña del usuario PostgreSQL. |
| `DB_HOST` | String | No | `localhost` | Host o IP del servidor PostgreSQL. |
| `DB_PORT` | Entero | No | `5432` | Puerto del servidor PostgreSQL. |
| `USE_SQLITE` | Booleano | No | `False` | Fuerza el uso del motor SQLite3 local (`db.sqlite3`). |
| `USE_S3` | Booleano | No | `False` | Habilita el almacenamiento de multimedia en Object Storage S3. |
| `AWS_ACCESS_KEY_ID` | String | Condicional | None | Identificador de clave de acceso S3 (requerido si `USE_S3=True`). |
| `AWS_SECRET_ACCESS_KEY` | String | Condicional | None | Clave secreta de acceso S3 (requerido si `USE_S3=True`). |
| `AWS_STORAGE_BUCKET_NAME` | String | Condicional | None | Nombre del bucket destino en el proveedor S3. |
| `AWS_S3_ENDPOINT_URL` | String URL | No | None | URL personalizada del endpoint S3 (para proveedores no-AWS). |
| `AWS_S3_REGION_NAME` | String | No | `us-east-1` | Region geografica del bucket S3. |
| `DATA_UPLOAD_MAX_MEMORY_SIZE` | Entero (Bytes)| No | `52428800` (50MB) | Tamano maximo del cuerpo de peticion HTTP en memoria. |
| `FILE_UPLOAD_MAX_MEMORY_SIZE` | Entero (Bytes)| No | `26214400` (25MB) | Tamano maximo de un archivo individual antes de volcado a disco. |
| `DATA_UPLOAD_MAX_NUMBER_FIELDS`| Entero | No | `2000` | Limite de parametros en formularios multiparte. |

---

### 5.2. Archivo .env de Ejemplo

```ini
# Configuracion del Nucleo Django
DJANGO_SECRET_KEY=clave-secreta-de-produccion-muy-segura-y-extensa-123456
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=api.codisecore.gob.ni,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://api.codisecore.gob.ni

# Base de Datos PostgreSQL
DATABASE_URL=postgresql://usuario_db:password_seguro@localhost:5432/codisecore_db

# Almacenamiento de Multimedia S3
USE_S3=True
AWS_ACCESS_KEY_ID=tu_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_access_key_aqui
AWS_STORAGE_BUCKET_NAME=codisecore-media-prod
AWS_S3_ENDPOINT_URL=https://s3.us-east-1.amazonaws.com
AWS_S3_REGION_NAME=us-east-1

# Limites de Carga Masiva (50MB request, 25MB por archivo)
DATA_UPLOAD_MAX_MEMORY_SIZE=52428800
FILE_UPLOAD_MAX_MEMORY_SIZE=26214400
DATA_UPLOAD_MAX_NUMBER_FIELDS=2000
```

---

## 6. Scripts y Comandos de Administracion

### 6.1. Despliegue con Docker y Docker Compose

#### Iniciar todos los servicios en segundo plano
```bash
docker compose up --build -d
```

#### Detener y remover contenedores y redes
```bash
docker compose down
```

#### Inspeccionar logs en tiempo real
```bash
docker compose logs -f web
docker compose logs -f nginx
```

#### Ejecutar comandos dentro del contenedor web
```bash
# Aplicar migraciones pendientes
docker compose exec web python manage.py migrate

# Crear una cuenta de superusuario
docker compose exec web python manage.py createsuperuser

# Abrir shell interactivo de Django
docker compose exec web python manage.py shell
```

---

### 6.2. Ejecucion y Desarrollo Local

#### Opcion A: Utilizando el gestor `uv` (Recomendado)
```bash
# Sincronizar el entorno virtual y dependencias
uv sync

# Ejecutar migraciones
uv run python manage.py migrate

# Iniciar servidor de desarrollo
uv run python manage.py runserver 0.0.0.0:8000
```

#### Opcion B: Utilizando entorno virtual estandar con `pip`
```bash
# Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -e .

# Ejecutar migraciones y arrancar servidor
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

---

### 6.3. Comandos de Mantenimiento de Django

```bash
# Crear nuevos archivos de migracion a partir de modelos modificados
python manage.py makemigrations codiselu

# Verificar el estado de las migraciones
python manage.py showmigrations

# Recolectar archivos estaticos para produccion
python manage.py collectstatic --noinput

# Ejecutar pruebas automatizadas
python manage.py test codiselu

# Verificacion de integridad del proyecto
python manage.py check --deploy
```

---

### 6.4. Flujo de Inicializacion (entrypoint.sh)

El archivo `entrypoint.sh` automatiza la sincronizacion del esquema de base de datos antes de transferir el control a Gunicorn:

```sh
#!/bin/sh
set -e

# Ejecuta migraciones automaticamente al encender el contenedor
python manage.py migrate --noinput

# Ejecuta el comando pasado por CMD en Dockerfile
exec "$@"
```

---

## 7. Catalogo y Ejemplos de Endpoints de la API

Base URL de la API:
- Desarrollo Directo: `http://localhost:8000/api/`
- Produccion / Proxy Nginx: `http://localhost/api/`

---

### 7.1. Autenticacion y Usuarios

#### 7.1.1. Registro de Usuario
- **Ruta**: `POST /api/auth/register/` (o `/api/register/`)
- **Autenticacion**: No requerida.
- **Payload de Solicitud**:
```json
{
  "username": "turista_explorador",
  "email": "turista@ejemplo.com",
  "password": "PasswordSeguro123!",
  "password_confirm": "PasswordSeguro123!",
  "first_name": "Carlos",
  "last_name": "Mendoza",
  "es_protagonista": false,
  "es_turista": true,
  "telefono": "+50588889999"
}
```
- **Respuesta Exitosa (`201 Created`)**:
```json
{
  "message": "Usuario registrado exitosamente.",
  "user": {
    "id": 4,
    "username": "turista_explorador",
    "email": "turista@ejemplo.com",
    "first_name": "Carlos",
    "last_name": "Mendoza",
    "es_protagonista": false,
    "es_turista": true,
    "telefono": "+50588889999",
    "foto_perfil": null,
    "is_staff": false,
    "is_active": true
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

#### 7.1.2. Inicio de Sesion (Login)
- **Ruta**: `POST /api/auth/login/` (o `/api/login/`)
- **Autenticacion**: No requerida.
- **Payload de Solicitud**:
```json
{
  "username": "turista_explorador",
  "password": "PasswordSeguro123!"
}
```
- **Respuesta Exitosa (`200 OK`)**:
```json
{
  "message": "Inicio de sesion exitoso.",
  "user": {
    "id": 4,
    "username": "turista_explorador",
    "email": "turista@ejemplo.com",
    "first_name": "Carlos",
    "last_name": "Mendoza",
    "es_protagonista": false,
    "es_turista": true,
    "telefono": "+50588889999",
    "foto_perfil": null,
    "is_staff": false,
    "is_active": true
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

#### 7.1.3. Refresco de Token JWT
- **Ruta**: `POST /api/auth/token/refresh/`
- **Autenticacion**: No requerida.
- **Payload de Solicitud**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
- **Respuesta Exitosa (`200 OK`)**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

#### 7.1.4. Perfil del Usuario Autenticado
- **Ruta**: `GET /api/auth/me/` | `PATCH /api/auth/me/`
- **Autenticacion**: Requerida (`Bearer <token>`).
- **Respuesta Exitosa (`200 OK`)**:
```json
{
  "id": 4,
  "username": "turista_explorador",
  "email": "turista@ejemplo.com",
  "first_name": "Carlos",
  "last_name": "Mendoza",
  "es_protagonista": false,
  "es_turista": true,
  "telefono": "+50588889999",
  "foto_perfil": "https://bucket.s3.amazonaws.com/perfiles/avatar.jpg",
  "is_staff": false,
  "is_active": true
}
```

---

#### 7.1.5. Autenticación con Google (Google Sign-In / OAuth2)
- **Ruta Principal**: `POST /api/auth/google/` (o `/api/google/`)
- **Rutas de Redirección**: `GET /api/auth/google/url/` | `GET /api/auth/google/callback/`
- **Autenticacion**: No requerida.
- **Guía de configuración en Google Cloud**: Ver [GUIA_GOOGLE_CLOUD_CONSOLE.md](GUIA_GOOGLE_CLOUD_CONSOLE.md).
- **Payload de Solicitud (desde Frontend/Móvil)**:
```json
{
  "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}
```
*(Acepta `"credential"`, `"id_token"` o `"code"`).*
- **Respuesta Exitosa (`200 OK`)**:
```json
{
  "message": "Autenticación con Google exitosa.",
  "is_new_user": false,
  "user": {
    "id": 5,
    "username": "usuario_google",
    "email": "usuario@gmail.com",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "foto_perfil": "http://localhost:8000/media/perfiles/google_avatar_5.jpg",
    "es_protagonista": false,
    "es_turista": true
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

### 7.2. Ciudades y Circuitos Creativos

#### 7.2.1. Listar Ciudades
- **Ruta**: `GET /api/ciudades/`
- **Autenticacion**: No requerida.
- **Respuesta Exitosa (`200 OK`)**:
```json
[
  {
    "id": 1,
    "nombre": "Leon",
    "descripcion": "Primera capital de la revolucion y ciudad universitaria con rica tradicion poetica e historica.",
    "imagen_portada": "https://bucket.s3.amazonaws.com/ciudades/portadas/leon.jpg",
    "latitud_centro": 12.43787,
    "longitud_centro": -86.87804,
    "circuitos": [
      {
        "id": 1,
        "ciudad": 1,
        "ciudad_nombre": "Leon",
        "nombre": "Ruta de los Murales y Poetas",
        "descripcion": "Recorrido por murales historicos y casas museo de grandes poetas leoneses.",
        "distancia_km": "3.50",
        "duracion_estimada": "2 horas",
        "dificultad": "Baja",
        "imagen_mapa": "https://bucket.s3.amazonaws.com/circuitos/mapas/ruta_murales.jpg",
        "puntos_interes": []
      }
    ],
    "datos_historicos": [],
    "galeria": []
  }
]
```

---

#### 7.2.2. Listar Circuitos Creativos
- **Ruta**: `GET /api/circuitos/` (o `/api/circuitos-creativos/`)
- **Autenticacion**: No requerida.
- **Parametros Query**: `?ciudad=1`
- **Respuesta Exitosa (`200 OK`)**:
```json
[
  {
    "id": 1,
    "ciudad": 1,
    "ciudad_nombre": "Leon",
    "nombre": "Ruta de los Murales y Poetas",
    "descripcion": "Recorrido por murales historicos y casas museo de grandes poetas leoneses.",
    "distancia_km": "3.50",
    "duracion_estimada": "2 horas",
    "dificultad": "Baja",
    "imagen_mapa": "https://bucket.s3.amazonaws.com/circuitos/mapas/ruta_murales.jpg",
    "puntos_interes": [
      {
        "id": 1,
        "circuito": 1,
        "circuito_nombre": "Ruta de los Murales y Poetas",
        "nombre": "Catedral de Leon",
        "descripcion": "Patrimonio de la Humanidad UNESCO, tumba de Ruben Dario.",
        "tipo": "Historico",
        "orden": 1,
        "latitud": 12.4356,
        "longitud": -86.8782,
        "datos_historicos": [],
        "galeria": []
      }
    ]
  }
]
```

---

### 7.3. Puntos de Interes y Datos Historicos

#### 7.3.1. Puntos de Interes (GIS)
- **Ruta**: `GET /api/puntos-interes/`
- **Autenticacion**: No requerida.
- **Respuesta Exitosa (`200 OK`)**:
```json
[
  {
    "id": 1,
    "circuito": 1,
    "circuito_nombre": "Ruta de los Murales y Poetas",
    "nombre": "Catedral de Leon",
    "descripcion": "Patrimonio de la Humanidad UNESCO.",
    "tipo": "Historico",
    "orden": 1,
    "latitud": 12.4356,
    "longitud": -86.8782,
    "datos_historicos": [
      {
        "id": 1,
        "ciudad": 1,
        "punto_interes": 1,
        "titulo": "Construccion de la Real Basilica Catedral",
        "tipo": "Hito",
        "contenido": "Construida entre 1747 y 1814 con estilo barroco sobrio.",
        "epoca_o_ano": "1747-1814"
      }
    ],
    "galeria": []
  }
]
```

---

#### 7.3.2. Datos Historicos, Mitos y Leyendas
- **Ruta**: `GET /api/datos-historicos/`
- **Autenticacion**: No requerida.
- **Respuesta Exitosa (`200 OK`)**:
```json
[
  {
    "id": 2,
    "ciudad": 1,
    "punto_interes": null,
    "titulo": "La Leyenda del Padre sin Cabeza",
    "tipo": "Leyenda",
    "contenido": "Mito colonial que recorre los atrios de las iglesias de Leon.",
    "epoca_o_ano": "Epoca Colonial (Siglo XVI)"
  }
]
```

---

### 7.4. Validacion de Visitas GPS

#### 7.4.1. Registrar Visita con Validacion Haversine
- **Ruta**: `POST /api/visitas/` (o `/api/usuario-puntos-visitados/`)
- **Autenticacion**: Requerida (`Bearer <token>`).
- **Payload de Solicitud**:
```json
{
  "punto_interes_id": 1,
  "latitud_usuario": 12.43565,
  "longitud_usuario": -86.87822
}
```
- **Respuesta Exitosa (`201 Created`)**:
```json
{
  "id": 15,
  "usuario": 4,
  "usuario_id": 4,
  "punto_interes": 1,
  "punto_interes_id": 1,
  "punto_interes_nombre": "Catedral de Leon",
  "circuito_nombre": "Ruta de los Murales y Poetas",
  "ciudad_nombre": "Leon",
  "fecha_visita": "2026-08-28T14:30:00Z",
  "latitud_usuario": 12.43565,
  "longitud_usuario": -86.87822,
  "es_validada": true,
  "distancia_metros": 6.82
}
```

---

#### 7.4.2. Consultar IDs de Puntos Visitados por el Turista
- **Ruta**: `GET /api/visitas/ids/` (o `/api/visitas/?ids_only=true`)
- **Autenticacion**: Requerida (`Bearer <token>`).
- **Respuesta Exitosa (`200 OK`)**:
```json
[1, 3, 7, 12]
```

---

### 7.5. Empresas y Protagonistas

#### 7.5.1. Listar Empresas
- **Ruta**: `GET /api/empresas/`
- **Autenticacion**: No requerida.
- **Parametros Query**: `?acepta_inversiones=true&ciudad=1`
- **Respuesta Exitosa (`200 OK`)**:
```json
[
  {
    "id": 1,
    "usuario": 2,
    "usuario_username": "artesanias_leonesas",
    "ciudad": 1,
    "ciudad_nombre": "Leon",
    "punto_interes": 1,
    "punto_interes_nombre": "Catedral de Leon",
    "nombre": "Taller de Ceramica Tradicional",
    "descripcion": "Elaboracion de piezas unicas de barro y ceramica policromada.",
    "categoria": "Taller",
    "direccion": "Costado sur de la Catedral",
    "telefono_contacto": "+50587654321",
    "email_contacto": "contacto@ceramicaleon.ni",
    "sitio_web": "https://ceramicaleon.ni",
    "imagen_portada": "https://bucket.s3.amazonaws.com/empresas/portadas/taller.jpg",
    "latitud": 12.4355,
    "longitud": -86.8781,
    "acepta_inversiones": true,
    "fecha_creacion": "2026-08-10T10:00:00Z"
  }
]
```

---

#### 7.5.2. Crear Empresa (Protagonista)
- **Ruta**: `POST /api/empresas/`
- **Autenticacion**: Requerida (`Bearer <token>`).
- **Payload de Solicitud**:
```json
{
  "ciudad": 1,
  "punto_interes": 1,
  "nombre": "Cafetin El Poeta",
  "descripcion": "Cafe de especialidad y reposteria tradicional leonesa.",
  "categoria": "Gastronomia",
  "direccion": "Frente al Parque Central",
  "telefono_contacto": "+50588887777",
  "email_contacto": "elpoeta@cafe.ni",
  "latitud": 12.4358,
  "longitud": -86.8785,
  "acepta_inversiones": true
}
```
- **Respuesta Exitosa (`201 Created`)**:
```json
{
  "id": 2,
  "usuario": 4,
  "usuario_username": "turista_explorador",
  "ciudad": 1,
  "ciudad_nombre": "Leon",
  "punto_interes": 1,
  "punto_interes_nombre": "Catedral de Leon",
  "nombre": "Cafetin El Poeta",
  "descripcion": "Cafe de especialidad y reposteria tradicional leonesa.",
  "categoria": "Gastronomia",
  "direccion": "Frente al Parque Central",
  "telefono_contacto": "+50588887777",
  "email_contacto": "elpoeta@cafe.ni",
  "sitio_web": null,
  "imagen_portada": null,
  "latitud": 12.4358,
  "longitud": -86.8785,
  "acepta_inversiones": true,
  "fecha_creacion": "2026-08-28T16:00:00Z"
}
```

---

### 7.6. Oportunidades e Inversiones Turisticas

#### 7.6.1. Listar Oportunidades de Inversion Activas
- **Ruta**: `GET /api/oportunidades-inversion/`
- **Autenticacion**: No requerida.
- **Parametros Query**: `?tipo_inversor=Nacional&empresa=1`
- **Respuesta Exitosa (`200 OK`)**:
```json
[
  {
    "id": 1,
    "empresa": 1,
    "empresa_nombre": "Taller de Ceramica Tradicional",
    "empresa_acepta_inversiones": true,
    "titulo": "Expansion de Hornos de Alta Temperatura",
    "descripcion": "Proyecto para duplicar la capacidad de produccion artesanal y crear area de exhibicion turistica.",
    "monto_requerido": "5000.00",
    "monto_minimo_inversion": "200.00",
    "monto_recaudado": "1200.00",
    "retorno_estimado": "12% anual o participacion en catalogo exclusivo",
    "tipo_inversor_permitido": "Todos",
    "esta_activa": true,
    "fecha_publicacion": "2026-08-15T09:00:00Z"
  }
]
```

---

#### 7.6.2. Enviar Oferta de Inversion
- **Ruta**: `POST /api/inversiones-turistas/`
- **Autenticacion**: Requerida (`Bearer <token>`).
- **Payload de Solicitud**:
```json
{
  "oportunidad": 1,
  "monto_propuesto": "500.00",
  "tipo_inversor": "Nacional",
  "mensaje": "Interesado en financiar la adquisicion de insumos para el area de exhibicion.",
  "telefono_inversor": "+50588889999",
  "email_inversor": "inversor@ejemplo.com"
}
```
- **Respuesta Exitosa (`201 Created`)**:
```json
{
  "id": 1,
  "inversionista": 4,
  "inversionista_username": "turista_explorador",
  "oportunidad": 1,
  "oportunidad_titulo": "Expansion de Hornos de Alta Temperatura",
  "empresa_id": 1,
  "empresa_nombre": "Taller de Ceramica Tradicional",
  "monto_propuesto": "500.00",
  "tipo_inversor": "Nacional",
  "mensaje": "Interesado en financiar la adquisicion de insumos para el area de exhibicion.",
  "telefono_inversor": "+50588889999",
  "email_inversor": "inversor@ejemplo.com",
  "estado": "Pendiente",
  "fecha_solicitud": "2026-08-28T16:15:00Z"
}
```

---

### 7.7. Eventos, Asistencias y Granos de Cafe

#### 7.7.1. Listar Eventos (con filtro de mural y oficiales)
- **Ruta**: `GET /api/eventos/`
- **Autenticacion**: No requerida.
- **Parametros Query**: `?en_mural=true&es_oficial=true&ciudad=1`
- **Respuesta Exitosa (`200 OK`)**:
```json
[
  {
    "id": 1,
    "creador": 1,
    "creador_username": "admin_cultural",
    "empresa": null,
    "empresa_nombre": null,
    "ciudad": 1,
    "ciudad_nombre": "Leon",
    "titulo": "Festival de Mitos y Leyendas Leonesas",
    "descripcion": "Gran desfile de gigantonas, el enano cabezon y representaciones teatrales populares.",
    "fecha_inicio": "2026-09-05T18:00:00Z",
    "fecha_fin": "2026-09-05T22:00:00Z",
    "ubicacion": "Plaza Parque Central Juan Jose Quezada",
    "latitud": 12.4357,
    "longitud": -86.8783,
    "imagen": "https://bucket.s3.amazonaws.com/eventos/festival_mitos.jpg",
    "precio_entrada": "0.00",
    "es_gratuito": true,
    "cupo_maximo": 500,
    "es_oficial": true,
    "dias_previos_mural": 7,
    "en_mural": true,
    "esta_activo": true,
    "total_granos_cafe": 48,
    "user_ha_dado_grano_cafe": false,
    "total_asistentes": 120,
    "user_va_a_asistir": false,
    "galeria": [],
    "publicaciones": [],
    "fecha_creacion": "2026-08-20T12:00:00Z"
  }
]
```

---

#### 7.7.2. Alternar Reaccion "Grano de Cafe"
- **Ruta**: `POST /api/eventos/{id}/grano-cafe/`
- **Autenticacion**: Requerida (`Bearer <token>`).
- **Respuesta Exitosa (`200 OK`)**:
```json
{
  "message": "Reaccion de grano de cafe agregada al evento.",
  "ha_dado_grano_cafe": true,
  "total_granos_cafe": 49
}
```

---

#### 7.7.3. Confirmar o Cancelar Asistencia a Evento
- **Ruta**: `POST /api/eventos/{id}/asistir/`
- **Autenticacion**: Requerida (`Bearer <token>`).
- **Respuesta Exitosa (`200 OK`)**:
```json
{
  "message": "Has registrado tu asistencia al evento.",
  "va_a_asistir": true,
  "total_asistentes": 121
}
```

---

### 7.8. Publicaciones, Galeria Masiva y Comentarios

#### 7.8.1. Listar Publicaciones del Feed Social
- **Ruta**: `GET /api/publicaciones/`
- **Autenticacion**: No requerida.
- **Parametros Query**: `?ciudad=1&empresa=1`
- **Respuesta Exitosa (`200 OK`)**:
```json
[
  {
    "id": 1,
    "autor": 2,
    "autor_username": "artesanias_leonesas",
    "autor_foto_perfil": "https://bucket.s3.amazonaws.com/perfiles/avatar2.jpg",
    "es_protagonista": true,
    "empresa": 1,
    "empresa_nombre": "Taller de Ceramica Tradicional",
    "ciudad": 1,
    "ciudad_nombre": "Leon",
    "evento": null,
    "evento_titulo": null,
    "titulo": "Nuevas piezas de coleccion colonial",
    "descripcion": "Acabamos de culminar una serie especial inspirada en las cupulas de la Catedral.",
    "imagen_principal": "https://bucket.s3.amazonaws.com/publicaciones/principal.jpg",
    "video_url": null,
    "imagenes": [
      {
        "id": 1,
        "imagen": "https://bucket.s3.amazonaws.com/publicaciones/colecciones/foto1.jpg",
        "fecha_creacion": "2026-08-28T11:00:00Z"
      },
      {
        "id": 2,
        "imagen": "https://bucket.s3.amazonaws.com/publicaciones/colecciones/foto2.jpg",
        "fecha_creacion": "2026-08-28T11:00:00Z"
      }
    ],
    "total_likes": 34,
    "user_ha_dado_like": true,
    "total_comentarios": 2,
    "comentarios": [
      {
        "id": 1,
        "publicacion": 1,
        "autor": 4,
        "autor_username": "turista_explorador",
        "autor_foto_perfil": null,
        "contenido": "Excelente trabajo artesanal. Estare visitando el taller este fin de semana.",
        "esta_activo": true,
        "fecha_creacion": "2026-08-28T12:00:00Z"
      }
    ],
    "esta_activa": true,
    "fecha_creacion": "2026-08-28T10:30:00Z"
  }
]
```

---

#### 7.8.2. Crear Publicacion con Subida Masiva de Imagenes (Multipart)
- **Ruta**: `POST /api/publicaciones/`
- **Autenticacion**: Requerida (`Bearer <token>`).
- **Encabezado HTTP**: `Content-Type: multipart/form-data`
- **Parametros Form-Data**:
  - `titulo` (texto): `"Visita increible al circuito"`
  - `descripcion` (texto): `"Fotografias del recorrido por las calles coloniales."`
  - `ciudad` (entero ID): `1`
  - `imagen_principal` (archivo binario): `[archivo_portada.jpg]`
  - `imagenes` (archivos binarios multiples - campo repetido): `[foto1.jpg]`, `[foto2.jpg]`, `[foto3.jpg]`
- **Ejemplo con cURL**:
```bash
curl -X POST http://localhost:8000/api/publicaciones/ \
  -H "Authorization: Bearer <access_token>" \
  -F "titulo=Visita increible al circuito" \
  -F "descripcion=Fotografias del recorrido por las calles coloniales." \
  -F "ciudad=1" \
  -F "imagen_principal=@/ruta/a/portada.jpg" \
  -F "imagenes=@/ruta/a/foto1.jpg" \
  -F "imagenes=@/ruta/a/foto2.jpg"
```
- **Respuesta Exitosa (`201 Created`)**: Retorna el objeto `Publicacion` creado con su coleccion anidada en `imagenes`.

---

#### 7.8.3. Alternar Like en Publicacion
- **Ruta**: `POST /api/publicaciones/{id}/like/`
- **Autenticacion**: Requerida (`Bearer <token>`).
- **Respuesta Exitosa (`200 OK`)**:
```json
{
  "message": "Like agregado a la publicacion.",
  "ha_dado_like": true,
  "total_likes": 35
}
```

---

#### 7.8.4. Agregar Comentario a Publicacion
- **Ruta**: `POST /api/publicaciones/{id}/comentarios/` (o `/api/comentarios-publicaciones/`)
- **Autenticacion**: Requerida (`Bearer <token>`).
- **Payload de Solicitud**:
```json
{
  "contenido": "Hermosa iniciativa, felicidades a los artesanos."
}
```
- **Respuesta Exitosa (`201 Created`)**:
```json
{
  "id": 3,
  "publicacion": 1,
  "autor": 4,
  "autor_username": "turista_explorador",
  "autor_foto_perfil": null,
  "contenido": "Hermosa iniciativa, felicidades a los artesanos.",
  "esta_activo": true,
  "fecha_creacion": "2026-08-28T16:45:00Z"
}
```

---

## 8. Contribucion

Las contribuciones son bienvenidas. Sigue este flujo de trabajo para colaborar en el desarrollo:

1. Realiza un Fork de este repositorio.
2. Crea una rama para tu nueva caracteristica o correccion:
   ```bash
   git checkout -b feature/nueva-caracteristica
   ```
3. Realiza tus modificaciones y confirma los cambios:
   ```bash
   git commit -m "feat: implementacion de nueva funcionalidad"
   ```
4. Envia los cambios a tu rama remota:
   ```bash
   git push origin feature/nueva-caracteristica
   ```
5. Abre un Pull Request para revision.

---

## 9. Autores y Agradecimientos

- **Ader Zeas** - Desarrollo Backend y Arquitectura de la API REST
- **Aurora Loza** - Aseguramiento de Calidad y Pruebas
- **Iniciativa Hackathon Nicaragua**

---

## 10. Licencia

Este proyecto esta bajo la Licencia [MIT](LICENSE).

```text
Copyright (c) 2026 Codisecore

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<div align="center">
  <sub>Desarrollado para el fortalecimiento del turismo cultural y las Ciudades Creativas de Nicaragua</sub>
</div>

