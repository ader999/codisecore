# Guía Paso a Paso: Configurar Google Auth en Google Cloud Console

Esta guía explica detalladamente cómo crear el proyecto, configurar la pantalla de consentimiento OAuth y generar el **Client ID** y **Client Secret** en Google Cloud para conectar la autenticación de Google con este backend Django.

---

## Requisitos Previos
* Una cuenta de Google ([Gmail](https://gmail.com) o Google Workspace).
* Acceso a [Google Cloud Console](https://console.cloud.google.com/).

---

## Paso 1: Crear o Seleccionar un Proyecto en Google Cloud

1. Ingresa a [https://console.cloud.google.com/](https://console.cloud.google.com/).
2. Inicia sesión con tu cuenta de Google.
3. En la barra superior azul, haz clic en el selector de proyectos (al lado del logo de *Google Cloud*).
4. En la ventana emergente, haz clic en el botón **PROYECTO NUEVO** (arriba a la derecha).
5. Asigna los datos:
   * **Nombre del proyecto:** `Codise Ciudades Creativas` (o el nombre que prefieras).
   * **Organización:** Puedes dejarlo en *Sin organización*.
6. Haz clic en **CREAR** y espera unos segundos mientras se aprovisiona.
7. Vuelve al selector de proyectos en la barra superior y asegúrate de **seleccionar el proyecto recién creado**.

---

## Paso 2: Configurar la Pantalla de Consentimiento OAuth (OAuth Consent Screen)

Google requiere definir qué información se mostrará a los usuarios cuando inicien sesión con su cuenta de Google.

1. En el menú de navegación izquierdo (icono de tres líneas o hamburguesa), ve a:
   **APIs y servicios** > **Pantalla de consentimiento de OAuth** (o busca *"OAuth consent screen"* en la barra de búsqueda superior).
2. **Tipo de usuario (User Type):**
   * Selecciona **Externo (External)** (permite que cualquier usuario con cuenta de Google/Gmail pueda autenticarse).
   * Haz clic en **CREAR**.
3. **Paso 1 del asistente: Información de la aplicación:**
   * **Nombre de la aplicación:** `Ciudades Creativas Nicaragua` (o `CodiseCore`).
   * **Correo electrónico de asistencia al usuario:** Selecciona tu correo electrónico de la lista desplegable.
   * **Logotipo de la aplicación:** *(Opcional)* Puedes subir el logo si lo deseas.
   * **Dominio de la aplicación:** *(Opcional en desarrollo)*.
   * **Datos de contacto del desarrollador:** Escribe tu correo electrónico para que Google te notifique sobre cambios en la API.
   * Haz clic en **GUARDAR Y CONTINUAR**.
4. **Paso 2 del asistente: Permisos (Scopes):**
   * Haz clic en **AGREGAR O QUITAR PERMISOS**.
   * Marca las casillas de los 3 permisos básicos esenciales:
     * `.../auth/userinfo.email` (Ver tu dirección de correo electrónico principal).
     * `.../auth/userinfo.profile` (Ver tu información personal básica, nombre y foto).
     * `openid` (Asociar tu información personal con tu cuenta de Google).
   * Haz clic en **ACTUALIZAR** (abajo en la tabla).
   * Haz clic en **GUARDAR Y CONTINUAR**.
5. **Paso 3 del asistente: Usuarios de prueba (Test Users):**
   > [!IMPORTANT]
   > Mientras la aplicación esté en estado de publicación **"En prueba" (Testing)**, solo los correos que agregues aquí podrán iniciar sesión.
   * Haz clic en **AGREGAR USUARIOS**.
   * Ingresa tu propio correo electrónico y los correos de tu equipo que harán pruebas durante el desarrollo/hackathon.
   * Haz clic en **AGREGAR**.
   * Haz clic en **GUARDAR Y CONTINUAR**.
6. **Paso 4 del asistente: Resumen:**
   * Revisa la información y haz clic en **VOLVER AL PANEL**.

---

## Paso 3: Crear las Credenciales OAuth 2.0 (Client ID y Client Secret)

1. En el menú lateral izquierdo, haz clic en **Credenciales** (Credentials).
2. En la parte superior, haz clic en **+ CREAR CREDENCIALES** y selecciona **ID de cliente de OAuth** (OAuth client ID).
3. **Tipo de aplicación:** Selecciona **Aplicación web** (Web application).
4. **Nombre:** `CodiseCore Web & API Client` (o el nombre que identifique a tu frontend/backend).
5. **Orígenes autorizados de JavaScript (Authorized JavaScript origins):**
   Son las URLs desde donde el navegador web o la SPA (React, Vue, etc.) ejecutará peticiones o el botón de Google:
   * Haz clic en **+ AGREGAR URI** y añade:
     * `http://localhost:5173` *(si usas Vite / React)*
     * `http://localhost:3000` *(si usas Create React App o Next.js)*
     * `http://127.0.0.1:8000` *(tu servidor Django local)*
     * `http://localhost:8000`
     * *(Si ya tienes el dominio de Railway o producción, por ejemplo: `https://tu-dominio.up.railway.app`, agrégalo también).*
6. **URIs de redireccionamiento autorizados (Authorized redirect URIs):**
   Son las URLs a las que Google puede redirigir al usuario con el código de autorización tras iniciar sesión:
   * Haz clic en **+ AGREGAR URI** y añade:
     * `http://localhost:8000/api/auth/google/callback/`
     * `http://127.0.0.1:8000/api/auth/google/callback/`
     * `http://localhost:5173/auth/callback` *(si tu frontend React gestiona la redirección)*
     * `https://tu-dominio.up.railway.app/api/auth/google/callback/` *(para producción en Railway)*
7. Haz clic en **CREAR**.

---

## Paso 4: Obtener las Credenciales y Configurarlas en el Proyecto

Aparecerá una ventana emergente titulada **Cliente de OAuth creado**:
1. Copia el **ID de cliente** (algo similar a: `123456789012-abcdef123456789.apps.googleusercontent.com`).
2. Copia el **Secreto de cliente** (algo similar a: `GOCSPX-abc123def456_xyz789`).

3. Abre el archivo [.env](file:///home/overader/Proyectos/python/Django/codisecore/.env) en este proyecto y pega tus credenciales:
```env
# Google OAuth 2.0 Credentials
GOOGLE_CLIENT_ID=123456789012-abcdef123456789.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456_xyz789
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback/
FRONTEND_URL=http://localhost:5173
```

> [!TIP]
> Si estás desplegando en **Railway**, asegúrate de añadir también estas 4 variables en la sección **Variables** del panel de tu servicio en Railway.

---

## Paso 5: Probar la Conexión

Una vez configuradas las variables en `.env`:

### Opción A: Probar con la URL de autorización
Visita en tu navegador o mediante `GET`:
```http
GET http://localhost:8000/api/auth/google/url/
```
Te responderá con la URL de autorización lista. Ábrela en el navegador; verás la pantalla oficial de inicio de sesión de Google con el nombre de tu proyecto.

### Opción B: Integración en Frontend (React / Vite)
En tu frontend en React con `@react-oauth/google`:
```jsx
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

function App() {
  const handleSuccess = async (credentialResponse) => {
    // credentialResponse.credential es el id_token
    const res = await fetch('http://localhost:8000/api/auth/google/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        credential: credentialResponse.credential
      })
    });
    const data = await res.json();
    console.log('Usuario autenticado:', data.user);
    console.log('Tokens JWT:', data.tokens);
    // Guarda data.tokens.access y data.tokens.refresh en localStorage
  };

  return (
    <GoogleOAuthProvider clientId="TU_GOOGLE_CLIENT_ID.apps.googleusercontent.com">
      <GoogleLogin onSuccess={handleSuccess} onError={() => console.log('Login Failed')} />
    </GoogleOAuthProvider>
  );
}
```

---

## Preguntas Frecuentes y Solución de Problemas

* **Error: `redirect_uri_mismatch`:**
  Ocurre si la URL desde la que se solicita la redirección no está agregada exactamente en **URIs de redireccionamiento autorizados** en Google Cloud Console. Verifica que la URL coincida caracter por caracter (incluyendo `http` vs `https` y la barra `/` final).
* **Error: `access_denied` / Aplicación no verificada:**
  Si estás en modo *Testing*, asegúrate de que la cuenta con la que intentas iniciar sesión esté agregada en la lista de **Usuarios de prueba (Test Users)**.
* **¿Es necesario pagar en Google Cloud?**
  No. Google Sign-In / OAuth 2.0 para autenticación de usuarios es un servicio **completamente gratuito** sin límite de usuarios para este caso de uso.
