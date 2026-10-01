# 7. Módulo de Inversiones

El módulo de inversiones conecta a las empresas y talleres turísticos que aceptan inversión (`acepta_inversiones: true`) con turistas e inversionistas nacionales o extranjeros interesados en capitalizar proyectos culturales y sostenibles en Nicaragua.

---

## 7.1 Publicar Oportunidad de Inversión (`POST /api/oportunidades-inversion/`)

Permite al propietario protagonista de una empresa publicar una ronda o propuesta de financiamiento.

* **Endpoint:** `POST /api/oportunidades-inversion/`
* **Headers:**
  * `Content-Type: application/json`
  * `Authorization: Bearer <JWT_TOKEN>` *(El usuario debe ser el dueño de la empresa asociada)*

### Validación Previa Crítica
> ⚠️ Si la empresa asignada en el campo `"empresa"` tiene configurado `"acepta_inversiones": false`, el servidor rechazará la solicitud inmediatamente retornando un error `400 Bad Request`.

### Parámetros del Body (JSON)
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

---

## 7.2 Registrar Postulación de Inversión (`POST /api/inversiones-turistas/`)

Permite a cualquier turista autenticado (nacional o internacional) enviar una propuesta formal de inversión hacia una oportunidad publicada.

* **Endpoint:** `POST /api/inversiones-turistas/`
* **Headers:**
  * `Content-Type: application/json`
  * `Authorization: Bearer <JWT_TOKEN>`

### Parámetros del Body (JSON)
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

### Respuesta Exitosa (`201 Created`)
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

## 7.3 Consultar Oportunidades e Inversiones (`GET`)

* **Listar Oportunidades Públicas:**
  ```bash
  GET /api/oportunidades-inversion/
  ```
* **Listar Inversiones Recibidas / Enviadas:**
  ```bash
  GET /api/inversiones-turistas/
  ```
  *(Requiere `Authorization: Bearer <token>`. Turistas observan sus ofertas enviadas; protagonistas ven las ofertas dirigidas a sus empresas).*

---

[⬅ Empresas y Destinos](06-empresas-destinos.md) | [Volver al Índice](README.md) | [Siguiente: Agenda de Eventos y Mural ➡](08-agenda-eventos.md)
