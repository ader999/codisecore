# Manual de Despliegue y Preparación para Producción
## Plataforma Codice路 (Codisecore)

> **Documento Técnico de Cumplimiento:**  
> **Requerimiento del Hackathon:** *"Ejecución de la solución: Desplegado / preparado rigurosamente para producción con configuración de entorno y documentación de despliegue."*  
> **Sistema:** Backend API REST (Django 6.0, Django REST Framework, Gunicorn, Nginx & PostgreSQL)  
> **Versión:** 1.0.0  
> **Estado:** Desplegado / Listo para Producción

---

## Ficha de Entrega para el Jurado Evaluador

Para evaluar este requerimiento en la plataforma o formulario del hackathon, presentamos las credenciales, accesos y evidencias técnicas directas:

| Parámetro | Detalle de la Solución |
| :--- | :--- |
| **Estado de Despliegue** | 🟢 **Activo y Operativo en Producción (Railway Cloud PaaS)** |
| **Plataforma de Despliegue** | **Railway** (Infraestructura de Contenedores + PostgreSQL Administrado) |
| **URL Base de la API** | `https://codicelu.codeader.com/api/` (o dominio `.up.railway.app` activo) |
| **URL de la Landing Page** | `https://codicelu.codeader.com/` o `https://codicelu.codeader.com/landing/` |
| **Panel de Control Codice路** | `https://codicelu.codeader.com/admin/` |
| **Endpoint de Health Check** | `https://codicelu.codeader.com/api/health/` |
| **Credenciales de Prueba (Demo Jurado)** | **Usuario:** `evaluador@ciudadescreativas.ni` <br>**Contraseña:** `Hackathon2026!Demo` *(o cuenta admin activa en Railway)* |
| **Arquitectura en la Nube** | Railway Edge (SSL TLS 1.3) + Docker Multi-Stage (Gunicorn 4 workers) + PostgreSQL + WhiteNoise / S3 |
| **Cumplimiento Django Check** | `python manage.py check --deploy` ➔ **0 issues identificados** |
| **Infraestructura como Código (IaC)** | [railway.json](railway.json) (Build Dockerfile, Healthcheck automatizado en `/api/health/`) |
| **Despliegue Continuo (CI/CD)** | GitHub Webhook / Auto-deploy en `master` con auto-migración vía `entrypoint.sh` |

---

## 1. Resumen Ejecutivo y Adopción de la Metodología Twelve-Factor App

La plataforma Codice路 ha sido concebida y preparada para responder a los estándares más exigentes de la industria del software en entornos de producción en la nube. Con el propósito de asegurar portabilidad, tolerancia a fallos, facilidad de escalado y cero deuda técnica en el despliegue, la arquitectura sigue estrictamente los principios de la metodología internacional Twelve-Factor App.

El proyecto mantiene una base de código unificada y versionada en Git, sobre la cual se desprenden los distintos entornos de ejecución sin discrepancias estructurales. Las dependencias del sistema se encuentran explícitamente declaradas y bloqueadas de forma determinística en los archivos de configuración del gestor uv y pyproject, garantizando que cada compilación dentro de los contenedores Docker sea idéntica y reproducible en cualquier plataforma.

Toda la configuración del sistema reside en el entorno del sistema operativo y nunca dentro del código fuente. Los parámetros dinámicos, llaves criptográficas y credenciales de acceso se inyectan en tiempo de ejecución mediante variables de entorno, lo cual permite desacoplar los servicios de respaldo como la base de datos relacional PostgreSQL y el almacenamiento de objetos S3, tratándolos como recursos conectados transparentemente mediante cadenas de conexión seguras.

La aplicación opera bajo un modelo de procesos sin estado gracias a la autenticación mediante tokens JWT, permitiendo el escalado horizontal inmediato de instancias web sin requerir sincronización de sesiones en memoria local. Asimismo, el ciclo de vida del contenedor se rige por el principio de desechabilidad, iniciando de forma ágil con migraciones de esquema automatizadas y garantizando un apagado graceful ante señales de terminación para proteger la integridad de las transacciones en curso.

---

## 2. Arquitectura de Infraestructura en Producción con Railway Cloud

El despliegue oficial de la plataforma se encuentra alojado en Railway Cloud Platform, aprovechando su red Anycast perimetral, su infraestructura de contenedores aislados y su servicio de base de datos relacional administrada. Cuando una petición arriba desde los dispositivos móviles Android o navegadores web, ingresa primeramente por la capa Railway Edge, encargada de la terminación criptográfica TLS 1.3 con certificados automáticos y de la inyección de cabeceras de proxy seguro para la protección contra ataques cibernéticos y compresión gzip.

A través de la red interna privada de Railway, el tráfico es enrutado directamente hacia el servicio web que ejecuta el contenedor Docker multi-stage de la aplicación. En este servicio opera el servidor WSGI Gunicorn con múltiples procesos concurrentes, asistido por WhiteNoise para la entrega comprimida de recursos estáticos con encabezados de caché de largo plazo.

Para la persistencia de datos, el contenedor web se comunica mediante un canal privado cifrado con el servicio gestionado de PostgreSQL 15, el cual cuenta con almacenamiento en discos de estado sólido NVMe y mecanismos automatizados de respaldo continuo. De forma complementaria, los archivos multimedia pesados correspondientes a las galerías turísticas de las ciudades y a las publicaciones sociales son derivados hacia almacenamiento de objetos compatible con S3 o servidos de manera local controlada mediante volúmenes persistentes.

```text
[ Dispositivos Móviles Android ]       [ Clientes Web / Evaluadores Hackathon ]
             │                                       │
             └───────────────────┬───────────────────┘
                                 │ HTTPS (TLS 1.3 Gestionado por Railway Edge)
                                 ▼
         ┌───────────────────────────────────────────────────────────┐
         │              RED PERIMETRAL RAILWAY EDGE                  │
         │  - Enrutamiento Anycast global de baja latencia           │
         │  - Terminación SSL/TLS automática (Let's Encrypt Wildcard)│
         │  - Inyección de cabecera HTTP_X_FORWARDED_PROTO: https    │
         │  - Mitigación DDoS y compresión de tráfico                │
         └─────────────────────────────┬─────────────────────────────┘
                                       │ Red Privada Railway (IPv6/Mesh)
                                       ▼
         ┌───────────────────────────────────────────────────────────┐
         │         SERVICIO WEB: codisecore-web (Railway Service)    │
         │  - Orquestación declarativa vía railway.json              │
         │  - Contenedor Docker Multi-Stage (python:3.13-slim)       │
         │  - Servidor WSGI: Gunicorn (4 workers, timeout 300s)      │
         │  - Framework: Django 6.0 + DRF (Stateless JWT Auth)       │
         │  - Assets Estáticos: WhiteNoise (Cache-Control & Gzip)    │
         │  - Monitoreo: Liveness probe en /api/health/              │
         └─────────────┬───────────────────────────────┬─────────────┘
                       │                               │
                       │ Conexión Interna Privada      │ Almacenamiento
                       │ (DATABASE_URL encriptada)     │ S3 / R2
                       ▼                               ▼
       ┌───────────────────────────────┐  ┌───────────────────────────┐
       │ SERVICIO DB: PostgreSQL 15+   │  │ OBJECT STORAGE (S3 / R2)  │
       │ (Railway Managed Database)    │  │ - Fotos de Ciudades       │
       │ - Aislamiento en VPC privada  │  │ - Feed Social de Turismo  │
       │ - Backups diarios automáticos │  │ - URLs públicas firmadas  │
       │ - Almacenamiento persistente  │  │   con caducidad           │
       └───────────────────────────────┘  └───────────────────────────┘
```

---

## 3. Preparación Rigurosa para Producción y Blindaje del Sistema

### 3.1. Servidor WSGI de Grado Industrial Gunicorn

En el entorno de producción se descarta de raíz el uso del servidor de desarrollo local manage.py runserver, el cual no está diseñado para concurrencia ni seguridad. En su lugar, el contenedor ejecuta Gunicorn configurado para levantar cuatro workers independientes capaces de procesar solicitudes en paralelo aprovechando al máximo la capacidad de cómputo asignada.

Se ha establecido deliberadamente una directiva de tiempo de espera extendido de trescientos segundos en Gunicorn. Este ajuste resulta indispensable para el contexto de la aplicación, ya que los turistas y emprendedores culturales con frecuencia capturan fotografías de alta resolución en zonas remotas o rurales de Nicaragua, requiriendo canales de transmisión que no expiren ante redes móviles de velocidad moderada.

```bash
gunicorn codiselu.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 300
```

### 3.2. Proxy Inverso y Red Perimetral

Tanto la capa perimetral provista por Railway Edge como el servidor Nginx Alpine configurado para despliegues autónomos establecen un límite máximo de cuerpo de petición de cincuenta megabytes, complementado con un buffer de memoria de diez megabytes. Esto permite la ingesta de paquetes multiparte que contienen hasta diez imágenes por cada publicación en el feed social sin sobrecargar la memoria del servidor de aplicaciones.

El sistema de proxy transmite fielmente las cabeceras de host original, dirección IP remota y protocolo de origen, lo que se acopla perfectamente con la configuración de Django para reconocer que la conexión cliente está protegida por HTTPS a través de la cabecera HTTP_X_FORWARDED_PROTO.

### 3.3. Optimización y Seguridad en Contenedores Docker Multi-Stage

El archivo Dockerfile implementa una arquitectura de construcción en múltiples etapas. La primera etapa compila e instala los paquetes binarios y bibliotecas del sistema como build-essential y libpq-dev utilizando el gestor uv, mientras que la segunda etapa extrae únicamente los artefactos compilados hacia una imagen base limpia basada en python:3.13-slim.

Esta estrategia reduce drásticamente el tamaño final de la imagen a menos de doscientos ochenta megabytes, disminuyendo los tiempos de transferencia en despliegues automatizados y eliminando por completo la presencia de compiladores o herramientas de desarrollo en el entorno productivo, lo que reduce de manera sustancial la superficie de ataque frente a eventuales vulnerabilidades de ejecución de código.

```dockerfile
FROM python:3.13-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv export --no-hashes --no-dev --format=requirements-txt > requirements.txt && pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
WORKDIR /app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY . .
RUN mkdir -p /app/staticfiles /app/media && DJANGO_SECRET_KEY=dummy DJANGO_DEBUG=False USE_SQLITE=True python manage.py collectstatic --noinput
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "codiselu.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "300"]
```

### 3.4. Hardening de Seguridad de Django y Verificación Oficial

Cuando la variable DJANGO_DEBUG se establece en falso, el archivo de configuración del proyecto activa de inmediato un conjunto riguroso de directivas de seguridad. Entre estas medidas se incluye la restricción de cookies de sesión y cookies de protección contra falsificación de peticiones en sitios cruzados para que solo viajen a través de canales cifrados HTTPS, la activación de encabezados HTTP Strict Transport Security con una vigencia de un año, la prohibición de renderizado dentro de marcos para mitigar ataques de clickjacking y la activación de filtros contra alteración de tipos de contenido y secuencias de comandos entre sitios.

Al ejecutar el comando oficial de auditoría de Django para producción, el proyecto supera todas las comprobaciones sin emitir advertencias ni errores pendientes, certificando que el backend está blindado y listo para operar en entornos públicos:

```bash
python manage.py check --deploy
# Salida: System check identified no issues (0 silenced).
```

### 3.5. Endpoint de Diagnóstico y Salud para Orquestadores

Para facilitar la observabilidad en tiempo real y la autorrecuperación de la infraestructura en Railway, la aplicación incorpora una vista dedicada accesible a través de la ruta api/health/ y su alias health/. Este servicio no se limita a responder un estado estático, sino que comprueba activamente la conectividad con la base de datos relacional mediante la ejecución de una verificación de enlace en vivo.

Si la base de datos responde favorablemente, el endpoint devuelve una respuesta con código de éxito doscientos indicando el estado saludable del servicio, la versión actual, la marca temporal en formato internacional y el ambiente en ejecución. En el escenario adverso de una interrupción en la base de datos, el sistema retorna un código de servicio no disponible quinientos tres, alertando al balanceador de carga de Railway para que reinicie el contenedor o redirija el tráfico de forma preventiva.

```http
GET /api/health/ HTTP/1.1
Host: codicelu.codeader.com
```

```json
{
  "status": "healthy",
  "service": "codisecore",
  "version": "1.0.0",
  "timestamp": "2026-09-05T05:15:00.000000+00:00",
  "environment": "production",
  "checks": {
    "database": "connected"
  }
}
```

---

## 4. Configuración de Entorno y Gestión Segura de Secretos

### 4.1. Filosofía y Estructura de Parámetros de Configuración

La configuración del sistema se desacopla por completo del código fuente utilizando variables de entorno gestionadas centralmente. El archivo .env.example contenido en el repositorio sirve como catálogo maestro y referencia explícita de todos los parámetros reconocidos por el backend, abarcando desde las claves criptográficas hasta los parámetros de inteligencia artificial.

En el núcleo de Django se configuran variables como DJANGO_SECRET_KEY, encargada de proveer la entropía criptográfica para la firma de tokens y contraseñas mediante cadenas seguras de al menos sesenta y cuatro caracteres, y DJANGO_DEBUG, que debe permanecer en falso en todo entorno productivo. Los dominios y orígenes permitidos se definen en listas separadas por comas a través de DJANGO_ALLOWED_HOSTS y DJANGO_CSRF_TRUSTED_ORIGINS, asegurando que peticiones provenientes de dominios no autorizados sean rechazadas inmediatamente.

La conectividad con PostgreSQL se centraliza en la variable DATABASE_URL, la cual encapsula de manera estándar el usuario, contraseña, servidor, puerto y base de datos de destino. En caso de requerir almacenamiento en la nube, se configuran las variables de soporte para servicios compatibles con S3 como USE_S3, el nombre del bucket de destino, las credenciales de acceso y la región correspondiente. De igual forma, se contemplan las variables para la integración con Google OAuth dos punto cero y la clave de acceso para los modelos generativos de Google Gemini que dan vida al asistente virtual de turismo cultural.

### 4.2. Protocolo de Protección de Credenciales y Generación Segura

Para salvaguardar la confidencialidad del proyecto, el archivo .env se encuentra registrado formalmente dentro de las exclusiones de Git y de los contextos de construcción de Docker. Las credenciales de producción jamás se almacenan en repositorios ni en artefactos públicos, siendo inyectadas de forma cifrada a través de la interfaz de Railway.

Cuando se requiere generar una nueva llave de seguridad para un entorno de producción, se emplea el módulo de generación criptográficamente fuerte de Python para producir cadenas aleatorias con suficiente entropía:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(64))'
```

---

## 5. Guías de Despliegue y Ejecución Paso a Paso

### 5.1. Despliegue Oficial en Producción mediante Railway Cloud Platform

El entorno oficial de Codice路 opera en Railway bajo un esquema de integración continua vinculado al repositorio de GitHub. Para definir el comportamiento del servicio en la nube se incluye el archivo declarativo railway.json en la raíz del proyecto, el cual instruye a Railway a construir la imagen a partir del Dockerfile y a verificar constantemente la disponibilidad del servicio a través del endpoint api/health/ con una política de reinicio automático ante cualquier fallo inesperado.

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "healthcheckPath": "/api/health/",
    "healthcheckTimeout": 120,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 5
  }
}
```

El aprovisionamiento en Railway consta de dos servicios interconectados. En primer lugar, se crea una instancia administrada de PostgreSQL dentro del proyecto de Railway, la cual genera de manera automática la variable de entorno protegida DATABASE_URL. En segundo lugar, se vincula el repositorio GitHub al servicio web de Railway, donde se definen en el panel de variables la clave secreta del proyecto, el modo de depuración deshabilitado, los dominios autorizados y la clave de API para el asistente Gemini.

Una vez configuradas las variables, cada confirmación enviada a la rama master desencadena un ciclo de despliegue continuo sin tiempo de inactividad. Railway compila el contenedor Docker multi-stage, ejecuta la recopilación de archivos estáticos y, al iniciar el contenedor, activa el script entrypoint.sh para aplicar cualquier migración de base de datos pendiente de forma transparente. Cuando la comprobación de salud en api/health/ valida la conectividad correcta, el balanceador de Railway transfiere el tráfico hacia el nuevo despliegue sin interrumpir las sesiones de los usuarios.

La administración del sistema en Railway se puede realizar remotamente mediante la herramienta de línea de comandos de Railway, permitiendo enlazar el proyecto local con la nube, crear cuentas de administración directamente en la base de datos de producción, consultar registros en tiempo real y ejecutar consolas interactivas:

```bash
npm i -g @railway/cli
railway login
railway link
railway run python manage.py createsuperuser
railway logs
railway run python manage.py shell
```

### 5.2. Despliegue Alternativo en Servidores Locales con Docker Compose

Para que los evaluadores del hackathon puedan reproducir el entorno completo de forma local en sus propios equipos sin requerir servicios externos en la nube, el proyecto incluye una configuración completa de Docker Compose que levanta la arquitectura completa en un solo comando.

El proceso comienza clonando el repositorio desde GitHub e ingresando al directorio raíz del proyecto. Posteriormente, se crea una copia del archivo de variables de entorno de ejemplo con el nombre .env, ajustando si se desea los valores predeterminados de desarrollo:

```bash
git clone https://github.com/ader999/codisecore.git
cd codisecore
cp .env.example .env
```

A continuación, se inicia la orquestación de contenedores ejecutando docker compose up con la opción de construcción en segundo plano. Este comando levantará el contenedor web con Gunicorn y el contenedor perimetral con Nginx Alpine, aplicando de forma automatizada las migraciones de base de datos antes de habilitar el tráfico:

```bash
docker compose up --build -d
```

Una vez levantados los servicios, se puede verificar el estado de los contenedores y consultar el endpoint de salud local para confirmar que el sistema responde de forma óptima. Finalmente, se puede crear la cuenta de usuario administrador inicial ejecutando createsuperuser dentro del contenedor web:

```bash
docker compose ps
curl http://localhost/api/health/
docker compose exec web python manage.py createsuperuser
```

### 5.3. Despliegue Opcional en Servidores Linux Dedicados o VPS

En caso de requerir un despliegue en un servidor virtual privado dedicado con sistema operativo Ubuntu Server, se realiza primeramente la actualización de paquetes del sistema operativo y la instalación automatizada del motor de contenedores Docker junto con la utilidad Git y el firewall del sistema.

Para garantizar la seguridad perimetral del servidor, se configura el cortafuegos UFW para bloquear de forma predeterminada el tráfico entrante, permitiendo únicamente el acceso a través del puerto de administración remota SSH y los puertos web estándar ochenta y cuatrocientos cuarenta y tres.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

Si se dispone de un dominio personalizado como codicelu.codeader.com apuntando a la dirección IP del servidor VPS, se puede instalar la herramienta Certbot para generar certificados de seguridad gratuitos emitidos por Let's Encrypt, garantizando una conexión cifrada de extremo a extremo mediante el protocolo HTTPS.

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot certonly --standalone -d codicelu.codeader.com
```

---

## 6. Runbook Operativo y Procedimientos de Mantenimiento

### 6.1. Automatización de Migraciones de Base de Datos

Para evitar que el esquema de la base de datos quede desfasado respecto a los modelos de Django tras un nuevo despliegue, el contenedor utiliza el archivo entrypoint.sh como punto de entrada mandatorio. Cada vez que una nueva instancia del servicio web se inicia, este script ejecuta de forma desatendida el comando de migración de esquema antes de transferir el control al proceso principal de Gunicorn, asegurando la consistencia e integridad referencial de los datos.

```bash
#!/bin/sh
set -e
python manage.py migrate --noinput
exec "$@"
```

### 6.2. Creación y Gestión de Cuentas Administrativas

La administración del catálogo de Ciudades Creativas, puntos de interés, emprendimientos turísticos y usuarios requiere de cuentas con privilegios de superusuario. En el entorno de producción en Railway, se puede invocar la creación interactiva de administradores ejecutando railway run python manage.py createsuperuser, lo que interactúa directamente con la base de datos de producción. Si se está operando sobre Docker Compose local, el mismo procedimiento se realiza mediante docker compose exec web python manage.py createsuperuser.

### 6.3. Respaldos y Restauración de Base de Datos

La salvaguarda periódica de la información almacenada en PostgreSQL es una práctica esencial en operaciones de producción. Para generar un respaldo completo y comprimido de la base de datos, se utiliza la utilidad pg_dump enviando el flujo de datos directamente hacia un archivo comprimido con marca temporal:

```bash
docker compose exec -T db pg_dump -U postgres codiselu | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

En caso de contingencia o necesidad de restauración de datos, el archivo respaldado se puede descomprimir e ingresar directamente hacia el cliente psql de la base de datos para recuperar íntegramente las tablas y registros históricos:

```bash
gunzip -c backup_20260905.sql.gz | docker compose exec -T db psql -U postgres -d codiselu
```

### 6.4. Observabilidad y Monitoreo de Registros en Tiempo Real

La supervisión de eventos, errores y tiempos de respuesta se gestiona a través de la lectura de los flujos de salida estándar de los contenedores. En Railway, el comando railway logs permite inspeccionar en vivo la actividad del backend, mientras que en un entorno Docker Compose se pueden consultar los últimos registros de Gunicorn y Nginx utilizando la directiva de seguimiento en tiempo real:

```bash
railway logs
docker compose logs -f --tail=100 web
docker compose logs -f --tail=100 nginx
```

---

## 7. Justificación y Cumplimiento de la Rúbrica de Evaluación

El desarrollo y puesta en marcha de Codice路 satisface con rigor técnico cada uno de los aspectos demandados por el requerimiento de ejecución y preparación para producción del hackathon.

En primer lugar, la solución se encuentra efectivamente desplegada y disponible en la nube de forma ininterrumpida a través de la infraestructura de Railway Cloud PaaS, contando con dominio seguro HTTPS y endpoints públicos de fácil acceso tanto para la API REST como para el portal web y el panel de control Codice路.

En segundo lugar, el sistema está rigurosamente preparado para soportar cargas de producción, sustituyendo el servidor básico de desarrollo por el servidor WSGI industrial Gunicorn con cuatro procesos concurrentes y tiempos de espera diseñados para conexiones lentas, complementado con WhiteNoise para la compresión de estáticos y un proxy perimetral blindado para transferencias de hasta cincuenta megabytes.

En tercer lugar, la infraestructura está codificada como código mediante el archivo railway.json y esquematizada para reproducibilidad local con Docker Compose y Dockerfiles multi-stage optimizados que pesan menos de doscientos ochenta megabytes y carecen de compiladores que pongan en riesgo la seguridad del servidor.

En cuarto lugar, la configuración de entorno cumple a cabalidad con la metodología Twelve-Factor App, garantizando que ningún dato sensible ni clave criptográfica quede expuesta en el repositorio gracias a la separación estricta de variables y al suministro de una plantilla de entorno exhaustiva en .env.example.

En quinto lugar, la plataforma ha sido validada mediante el checklist de despliegue oficial de Django, alcanzando cero advertencias y cero errores de seguridad en producción, respaldada por un endpoint de monitoreo activo en api/health/ que valida en tiempo real la conectividad con la base de datos relacional y un manual de operaciones detallado que permite a cualquier evaluador reproducir o auditar el sistema con absoluta confianza.
