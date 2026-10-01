# 5. Visitas y Geolocalización GPS

Este módulo permite a los turistas registrar de forma verificada su visita física a los diferentes puntos de interés de los circuitos turísticos. El backend calcula automáticamente la proximidad física del turista respecto a las coordenadas reales del punto.

---

## 5.1 Mecanismo de Validación Geográfica (Haversine)

Cuando la aplicación móvil o web envía las coordenadas del dispositivo (`latitud_usuario` y `longitud_usuario`), el backend ejecuta la fórmula trigonométrica de Haversine para computar la distancia en línea recta:

* **Tolerancia:** Si la distancia entre el usuario y el punto de interés es menor o igual a **200 metros**, la visita se marca automáticamente como verificada (`"es_validada": true`).
* **Insignias y Progreso:** Permite a la app desbloquear medallas o logros turísticos únicamente cuando la visita es física y comprobada.

---

## 5.2 Registrar Punto Visitado (`POST /api/visitas/`)

Registra la visita del usuario autenticado a un punto de interés turístico.

* **Endpoint:** `POST /api/visitas/`
* **Headers:** 
  * `Content-Type: application/json`
  * `Authorization: Bearer <JWT_TOKEN>`

### Body con Coordenadas GPS (Recomendado)
```json
{
  "punto_interes_id": 1,
  "latitud_usuario": 12.4351,
  "longitud_usuario": -86.8789
}
```

### Respuesta Exitosa (`201 Created`)
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

---

## 5.3 Obtener Historial de Visitas (`GET /api/visitas/`)

Obtiene el listado detallado con fecha, nombres y estados de todas las visitas del usuario autenticado.

* **Endpoint:** `GET /api/visitas/`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`

---

## 5.4 Obtener IDs de Puntos Visitados (`GET /api/visitas/ids/`)

Endpoint ligero y de alto rendimiento diseñado especialmente para aplicaciones móviles. Retorna una lista plana con los números de ID de los puntos visitados por el usuario. Permite cambiar el color o icono de los marcadores en el mapa rápidamente.

* **Endpoint:** `GET /api/visitas/ids/`
* **Headers:** `Authorization: Bearer <JWT_TOKEN>`
* **Respuesta Exitosa (200 OK):**

```json
[1, 3, 7, 14]
```

---

[⬅ Catálogo Turístico](04-catalogo-turistico.md) | [Volver al Índice](README.md) | [Siguiente: Empresas y Destinos ➡](06-empresas-destinos.md)
