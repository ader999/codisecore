# 10. Asistente Virtual Turístico Inteligente "Eduardo" (Gemini AI)

La plataforma cuenta con **Eduardo**, un asistente virtual turístico inteligente impulsado por modelos **Google Gemini** con tecnología de **Function Calling (Tool Calling)** en tiempo real. 

A diferencia de un chatbot convencional, Eduardo tiene acceso directo a la base de datos oficial de Nicaragua en tiempo real: consulta ciudades creativas, circuitos, puntos de interés, eventos, talleres, datos históricos y empresas locales mediante herramientas programadas.

---

## 10.1 Configuración de Modelos y Fallback Automático

* **Modelo principal:** `gemini-3.1-flash-lite` (Ultra-rápido y optimizado para respuestas conversacionales en aplicaciones móviles).
* **Modelo de respaldo (Fallback automático):** `gemini-3.8-flash` (Se activa de forma transparente e instantánea si el modelo principal experimenta sobrecarga temporal o cuotas agotadas).
* **Configuración del servidor:** Se configura mediante la variable de entorno `GEMINI_API_KEY` en el archivo `.env`.

---

## 10.2 Endpoint de Conversación

* **Endpoint Principal:** `POST /api/asistente/chat/`
* **Endpoint Alias:** `POST /api/asistente/`
* **Autenticación:** Opcional. 
  * Si el turista está autenticado, envía la cabecera `Authorization: Bearer <access_token>` para que Eduardo conozca su nombre y rol (Turista o Protagonista).
  * Si no está autenticado, funciona de forma pública y abierta para cualquier visitante.
* **Headers:**
  * `Content-Type: application/json`
  * `Authorization: Bearer <access_token>` *(Opcional)*
  * `Accept-Language: es` *(Opcional: `es`, `en`, `zh`)*

---

## 10.3 Parámetros del Body (JSON)

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `mensaje` | `String` | **Sí** | La pregunta o mensaje del usuario (ej: "¿Qué puedo hacer en Masaya en 2 horas?"). |
| `idioma` | `String` | No | Código de idioma deseado: `"es"` (español), `"en"` (inglés), `"zh"` (mandarín). Por defecto `"es"`. |
| `ubicacion` | `Object` | No | Coordenadas GPS actuales del dispositivo: `{"latitud": 11.9344, "longitud": -85.9560}`. Permite a Eduardo invocar `buscar_puntos_cercanos` automáticamente. |
| `historial` | `Array` | No | Lista de turnos de diálogo previos para mantener contexto en el hilo: `[{"role": "user", "parts": ["..."]}, {"role": "model", "parts": ["..."]}]`. |

---

## 10.4 Ejemplos de Petición y Respuesta

### Ejemplo 1: Consulta básica con recomendación de circuitos y eventos
**Petición (`POST /api/asistente/chat/`):**
```json
{
  "mensaje": "¿Qué circuitos turísticos me recomiendas en Granada y qué dificultad tienen?",
  "idioma": "es"
}
```

**Respuesta Exitosa (`200 OK`):**
```json
{
  "nombre_asistente": "Eduardo",
  "respuesta": "¡Hola! Soy Eduardo, tu guía virtual en las Ciudades Creativas de Nicaragua. En la hermosa ciudad colonial de **Granada** te recomiendo los siguientes circuitos creativos:\n\n1. **Ruta Colonial y Casonas Históricas**:\n   - **Dificultad:** Baja (ideal para caminatas familiares).\n   - **Distancia:** 2.5 km (aproximadamente 1.5 horas).\n   - **Puntos clave:** Parque Central de Granada, Catedral de Granada y Convento San Francisco.\n\n2. **Circuito Artesanal y Tradiciones**:\n   - **Dificultad:** Media.\n   - **Distancia:** 4.2 km.\n   - **Puntos clave:** Talleres locales y malecón del Gran Lago.\n\n¿Te gustaría conocer los horarios de algún punto de interés específico o buscar restaurantes cercanos?",
  "herramientas_utilizadas": [
    {
      "nombre": "buscar_circuitos",
      "argumentos": {
        "ciudad": "Granada"
      }
    }
  ],
  "modelo_utilizado": "gemini-3.1-flash-lite",
  "idioma": "es",
  "puntos_interes_ids": [1, 2]
}
```

---

### Ejemplo 2: Consulta geolocalizada (Sitios turísticos cercanos vía GPS)
Cuando la aplicación móvil cuenta con permisos de geolocalización, puede adjuntar el nodo `ubicacion`. Eduardo ejecutará la herramienta de búsqueda por radio geográfico:

**Petición (`POST /api/asistente/chat/`):**
```json
{
  "mensaje": "¿Qué atractivos turísticos o talleres tengo cerca de donde estoy parado?",
  "idioma": "es",
  "ubicacion": {
    "latitud": 11.9744,
    "longitud": -86.0942
  }
}
```

**Respuesta (`200 OK`):**
```json
{
  "respuesta": "Según tu ubicación actual en Masaya, tienes estos puntos a pocos minutos:\n\n* **Taller Escuela de Hamacas Monimbó** (a 0.4 km): Taller artesanal con demostración de tejido tradicional.\n* **Mercado de Artesanías de Masaya** (a 1.1 km): Gran variedad de artesanías, cuero, madera y dulces típicos.\n* **Mirador de Catarina** (a 4.8 km): Hermosa vista hacia la Laguna de Apoyo.\n\n¿Deseas indicaciones o información de horarios de alguno?",
  "herramientas_utilizadas": [
    {
      "nombre": "buscar_puntos_cercanos",
      "argumentos": {
        "latitud": 11.9744,
        "longitud": -86.0942,
        "radio_km": 5.0
      }
    }
  ],
  "modelo_utilizado": "gemini-3.1-flash-lite",
  "idioma": "es",
  "puntos_interes_ids": [5, 8, 14]
}
```

---

### Ejemplo 3: Preguntas Internacionales (Inglés y Mandarín)

**Petición en Inglés:**
```json
{
  "mensaje": "What cultural events are happening this month in Leon?",
  "idioma": "en"
}
```

**Petición en Chino Mandarín:**
```json
{
  "mensaje": "莱昂市有什么推荐的旅游路线吗？",
  "idioma": "zh"
}
```

---

### Ejemplo 4: Conversación con Historial de Mensajes
Para mantener el hilo conversacional, el cliente reenvía el array `historial`:

```json
{
  "mensaje": "¿A qué hora abre la catedral?",
  "historial": [
    {
      "role": "user",
      "parts": ["¿Qué lugares puedo visitar en León?"]
    },
    {
      "role": "model",
      "parts": ["En León puedes visitar la Insigne y Real Basílica Catedral de la Asunción y el Centro de Arte Fundación Ortiz Gurdián."]
    }
  ],
  "idioma": "es"
}
```

---

## 10.5 Códigos de Estado y Manejo de Errores

| Código HTTP | Código Interno | Causa y Acción Correctiva |
| :--- | :--- | :--- |
| **`200 OK`** | Ninguno | Petición procesada exitosamente por el asistente. |
| **`400 Bad Request`** | `MENSAJE_REQUERIDO` | El campo `mensaje` estaba ausente o en blanco. |
| **`503 Service Unavailable`** | `GEMINI_NO_CONFIGURADO` | Falta configurar la variable `GEMINI_API_KEY` en el archivo `.env`. |
| **`500 Internal Server Error`** | `ERROR_ASISTENTE_IA` | Ocurrió un error inesperado al conectar con los modelos de Google. |

---

## 10.6 Implementación en Kotlin (Android Nativo)

A continuación se muestra un servicio completo con **Retrofit** y **Coroutines**:

```kotlin
// 1. Modelos de datos
data class ChatRequest(
    val mensaje: String,
    val idioma: String = "es",
    val ubicacion: UbicacionGps? = null,
    val historial: List<ChatHistoryItem>? = null
)

data class UbicacionGps(
    val latitud: Double,
    val longitud: Double
)

data class ChatHistoryItem(
    val role: String, // "user" o "model"
    val parts: List<String>
)

data class ChatResponse(
    val nombre_asistente: String,
    val respuesta: String,
    val herramientas_utilizadas: List<Map<String, Any>>,
    val modelo_utilizado: String,
    val idioma: String,
    val puntos_interes_ids: List<Int> = emptyList()
)

// 2. Definición del servicio Retrofit
interface AsistenteApiService {
    @POST("api/asistente/chat/")
    suspend fun enviarMensaje(
        @Header("Authorization") authHeader: String? = null,
        @Body request: ChatRequest
    ): retrofit2.Response<ChatResponse>

    // Obtener tarjetas interactivas de los puntos recomendados en lote:
    @GET("api/puntos-interes/")
    suspend fun obtenerTarjetasPuntos(
        @Query("ids") idsCsv: String
    ): retrofit2.Response<List<PuntoInteresDto>>
}

// 3. Llamada desde ViewModel o Repository
suspend fun preguntarAlAsistente(
    pregunta: String,
    latitud: Double?,
    longitud: Double?,
    historialPrevio: List<ChatHistoryItem>
): String? {
    val ubicacion = if (latitud != null && longitud != null) {
        UbicacionGps(latitud, longitud)
    } else null

    val body = ChatRequest(
        mensaje = pregunta,
        idioma = "es",
        ubicacion = ubicacion,
        historial = historialPrevio
    )

    val response = apiService.enviarMensaje(request = body)
    return if (response.isSuccessful) {
        response.body()?.respuesta
    } else {
        null
    }
}
```

---

## 10.7 Ejemplo con cURL

```bash
curl -X POST "http://localhost:8000/api/asistente/chat/" \
     -H "Content-Type: application/json" \
     -d '{
       "mensaje": "¿Cuáles son los eventos culturales más importantes de este mes?",
       "idioma": "es"
     }'
```

---

[⬅ Publicaciones y Comentarios](09-publicaciones-comentarios.md) | [Volver al Índice](README.md) | [Siguiente: Ejemplos de Integración ➡](11-ejemplos-integracion-clientes.md)
