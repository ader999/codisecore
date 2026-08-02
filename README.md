# Codisecore

Backend en Django para la gestión de ciudades y circuitos creativos turísticos.

## Descripción

Codisecore (Codiselu) es una API REST que permite administrar usuarios, ciudades y circuitos creativos con información geográfica, imágenes y niveles de dificultad.

## Tecnologías

- Python 3.13
- Django 6
- Django REST Framework
- PostgreSQL
- Docker

## Requisitos

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) (opcional, para gestión de dependencias)
- Docker y Docker Compose (para despliegue con contenedores)

## Instalación

### Con Docker

```bash
docker compose up --build
```

La aplicación estará disponible en `http://localhost:8000`.

### Desarrollo local

```bash
uv sync
python manage.py migrate
python manage.py runserver
```

## Colaboradores

- **Aurora Loza** — colaboradora

## Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).

Copyright (c) 2026 Codisecore

Se concede permiso, de forma gratuita, a cualquier persona que obtenga una copia de este software y de los archivos de documentación asociados, para usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar y/o vender copias del software, sujeto a las condiciones de la licencia MIT.
