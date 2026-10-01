# 2. Autenticación (JWT y Google Sign-In)

Aunque los endpoints de consulta pública del catálogo turístico no requieren credenciales, las acciones protegidas (registro de visitas, publicación de contenido, postulación de inversiones o creación de eventos) requieren autenticación mediante tokens **JWT (JSON Web Tokens)** o **Google Sign-In / OAuth2**.

---

## 2.1 Iniciar Sesión con Credenciales (JWT)

Permite autenticarse mediante usuario/contraseña para obtener un par de tokens criptográficos (`access` y `refresh`).

* **Endpoint:** `POST /api/auth/login/` *(o alias `POST /api/login/`)*
* **Headers:** `Content-Type: application/json`
* **Body (JSON):**

```json
{
  "username": "carlos_turista",
  "password": "Pass1234!"
}
```

* **Respuesta Exitosa (200 OK):**

```json
{
  "message": "Inicio de sesión exitoso.",
  "user": {
    "id": 2,
    "username": "carlos_turista",
    "email": "carlos@example.com",
    "es_protagonista": false,
    "es_turista": true
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
  }
}
```

---

## 2.2 Enviar Token en Peticiones Protegidas

Para cualquier petición a endpoints protegidos, incluye el token de acceso en la cabecera `Authorization` utilizando el esquema Bearer:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

---

## 2.3 Autenticación con Google (Google Sign-In / OAuth2)

Permite que los usuarios inicien sesión o se registren automáticamente utilizando su cuenta institucional o personal de Google. Si el usuario no existe previamente en la base de datos, el sistema lo crea de forma automática con su nombre, apellido, correo electrónico y foto de perfil proveniente de Google.

> 📘 **Configuración en la Nube:**  
> Consulta la [Guía de Google Cloud Console](../../GUIA_GOOGLE_CLOUD_CONSOLE.md) para generar el `Client ID` y `Client Secret`.

### 1. Iniciar Sesión / Registro con Google (Frontend SPA o Móvil)

* **Endpoint:** `POST /api/auth/google/` *(o alias `POST /api/google/`)*
* **Body (JSON):**

```json
{
  "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}
```

*(Nota: También acepta la clave `"id_token"` en lugar de `"credential"`, o un `"code"` de autorización OAuth2).*

* **Respuesta Exitosa (200 OK):**

```json
{
  "message": "Autenticación con Google exitosa.",
  "is_new_user": false,
  "user": {
    "id": 5,
    "username": "maria_gonzalez",
    "email": "maria.gonzalez@gmail.com",
    "first_name": "María",
    "last_name": "González",
    "foto_perfil": "http://localhost:8000/media/perfiles/google_avatar_5.jpg",
    "es_protagonista": false,
    "es_turista": true
  },
  "tokens": {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
  }
}
```

### 2. Flujo de Redirección Navegador (Opcional)

Si utilizas un flujo web estándar de redirección:

* **Obtener URL de Consentimiento:** `GET /api/auth/google/url/`
* **Callback de Redirección:** `GET /api/auth/google/callback/?code=...`  
  *(Al visitarse desde el navegador, redirige a `FRONTEND_URL/auth/callback?access=...&refresh=...`)*.

### 3. Ejemplo de Integración en React (Vite / Next.js)

Instalación de la librería oficial de Google OAuth:

```bash
npm install @react-oauth/google
```

Componente de autenticación:

```jsx
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

export function GoogleAuthButton() {
  const handleSuccess = async (credentialResponse) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/google/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: credentialResponse.credential }),
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        console.log('Bienvenido:', data.user.first_name);
      }
    } catch (error) {
      console.error('Error autenticando con Google:', error);
    }
  };

  return (
    <GoogleOAuthProvider clientId="TU_GOOGLE_CLIENT_ID.apps.googleusercontent.com">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={() => console.error('Falló el inicio de sesión con Google')}
      />
    </GoogleOAuthProvider>
  );
}
```

---

[⬅ Configuración Base](01-configuracion-base.md) | [Volver al Índice](README.md) | [Siguiente: Resumen de Endpoints ➡](03-resumen-endpoints.md)
