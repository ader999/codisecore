# 11. Ejemplos de Integración y Clientes

Esta sección compila plantillas listas para usar en los lenguajes y frameworks más utilizados por desarrolladores frontend y móviles al consumir la API de **Ciudades Creativas**.

---

## 11.1 JavaScript (Fetch API / Async Await - Web o React)

Plantilla para aplicaciones web (React, Vue, Svelte, Vanilla JS) utilizando promesas nativas:

```javascript
const API_BASE_URL = 'http://localhost:8000/api';

// 1. Obtener catálogo de Ciudades Creativas con soporte de idioma
async function obtenerCiudades(idioma = 'es') {
  try {
    const response = await fetch(`${API_BASE_URL}/ciudades/`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Accept-Language': idioma,
      },
    });

    if (!response.ok) {
      throw new Error(`Error HTTP: ${response.status}`);
    }

    const ciudades = await response.json();
    console.log(`Total de ciudades cargadas: ${ciudades.length}`);
    return ciudades;
  } catch (error) {
    console.error('Error al consultar ciudades:', error);
    throw error;
  }
}

// 2. Realizar petición autenticada (ejemplo: registrar visita)
async function registrarVisita(token, puntoId, latitud, longitud) {
  const response = await fetch(`${API_BASE_URL}/visitas/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      punto_interes_id: puntoId,
      latitud_usuario: latitud,
      longitud_usuario: longitud,
    }),
  });

  return await response.json();
}
```

---

## 11.2 Dart / Flutter (Aplicaciones Móviles Android e iOS)

Integración móvil con el paquete `http`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiClient {
  // En emulador Android usar 10.0.2.2 en lugar de localhost
  static const String baseUrl = 'http://10.0.2.2:8000/api';

  // Obtener ciudades con soporte de localización
  static Future<List<dynamic>> fetchCiudades({String lang = 'es'}) async {
    final url = Uri.parse('$baseUrl/ciudades/');
    final response = await http.get(
      url,
      headers: {
        'Accept-Language': lang,
        'Accept': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    } else {
      throw Exception('Fallo al obtener ciudades: ${response.statusCode}');
    }
  }

  // Registrar visita verificada con GPS
  static Future<Map<String, dynamic>> registrarVisita({
    required String token,
    required int puntoId,
    required double latitud,
    required double longitud,
  }) async {
    final url = Uri.parse('$baseUrl/visitas/');
    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'punto_interes_id': puntoId,
        'latitud_usuario': latitud,
        'longitud_usuario': longitud,
      }),
    );

    return jsonDecode(utf8.decode(response.bodyBytes));
  }
}
```

---

## 11.3 Python (Librería `requests`)

Ideal para scripts de automatización, pruebas de carga o ingesta de datos:

```python
import requests

BASE_URL = "http://localhost:8000/api"

def consultar_ciudades():
    headers = {"Accept-Language": "es"}
    response = requests.get(f"{BASE_URL}/ciudades/", headers=headers)
    
    if response.status_code == 200:
        ciudades = response.json()
        print(f"Total de Ciudades: {len(ciudades)}")
        for c in ciudades:
            print(f"- {c['nombre']}: {len(c.get('circuitos', []))} circuitos.")
        return ciudades
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def iniciar_sesion(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/auth/login/", json=payload)
    if response.status_code == 200:
        data = response.json()
        return data["tokens"]["access"]
    raise Exception("Credenciales incorrectas")

if __name__ == "__main__":
    consultar_ciudades()
```

---

## 11.4 Comandos cURL para Pruebas Rápidas

```bash
# 1. Consultar ciudades en español
curl -X GET http://localhost:8000/api/ciudades/ -H "Accept-Language: es"

# 2. Consultar ciudades en inglés
curl -X GET http://localhost:8000/api/ciudades/ -H "Accept-Language: en"

# 3. Consultar sólo circuitos
curl -X GET http://localhost:8000/api/circuitos/

# 4. Iniciar sesión y capturar token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "carlos_turista", "password": "Pass1234!"}'

# 5. Consultar eventos activos en el mural
curl -X GET "http://localhost:8000/api/eventos/?en_mural=true"
```

---

[⬅ Asistente Virtual IA](10-asistente-ia-eduardo.md) | [Volver al Índice](README.md)
