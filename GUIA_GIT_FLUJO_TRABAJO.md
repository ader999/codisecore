# 🚀 Guía de Flujo de Trabajo en Git (Git Workflow)

Esta guía documenta el estándar profesional de control de versiones del proyecto **Codisecore**, garantizando:
- Ramas organizadas y estructuradas.
- Mensajes bajo la especificación **Conventional Commits**.
- Trazabilidad y convergencia limpia mediante **Pull Requests**.
- Pasos exactos para cuando se vaya a comitear cualquier nuevo cambio.

---

## 🌳 1. Estructura y Jerarquía de Ramas

El proyecto utiliza un modelo de 3 capas organizadas:

```mermaid
gitGraph
    commit id: "Base"
    branch beta
    checkout beta
    branch feature/nueva-funcionalidad
    checkout feature/nueva-funcionalidad
    commit id: "feat: codigo"
    commit id: "test: pruebas"
    checkout beta
    merge feature/nueva-funcionalidad id: "PR: Feature -> Beta" tag: "v1.X.X-beta"
    checkout master
    merge beta id: "PR: Beta -> Master" tag: "v1.X.X"
```

| Rama | Propósito | ¿Se commitea directo? | Origen de la rama |
| :--- | :--- | :---: | :--- |
| **`master`** | **Producción**: Código 100% probado, auditado y listo para usuarios finales. | ❌ No (solo PR desde `beta`) | Rama inicial |
| **`beta`** | **Staging / Integración**: Entorno de pruebas conjuntas (QA) y pre-lanzamiento. | ❌ No (solo PR desde `feature/*`) | Nace de `master` |
| **`feature/*`** | **Desarrollo**: Aislamiento de nuevas funcionalidades, endpoints o módulos. | ✅ Sí | Nace de `beta` |
| **`fix/*`** | **Corrección**: Corrección de bugs detectados durante pruebas en beta. | ✅ Sí | Nace de `beta` |
| **`hotfix/*`** | **Urgencias**: Parches críticos directos sobre producción. | ✅ Sí | Nace de `master` |

---

## 🏷️ 2. Convención de Nombres para Ramas

Cuando vayas a crear una rama para un nuevo cambio o funcionalidad, utiliza el prefijo correspondiente:

- `feature/<nombre-en-kebab-case>`: Para nuevas funciones.
  - *Ejemplos:* `feature/rutas-turisticas`, `feature/notificaciones-push`, `feature/pasarela-pagos`.
- `fix/<nombre-del-bug>`: Para corregir errores o fallos detectados.
  - *Ejemplos:* `fix/error-token-expirado`, `fix/filtro-ciudades`.
- `docs/<nombre-tema>`: Para cambios exclusivos de documentación.
  - *Ejemplos:* `docs/actualizar-swagger`, `docs/guia-despliegue`.
- `test/<nombre-modulo>`: Para añadir pruebas automatizadas.
  - *Ejemplos:* `test/suite-comentarios`.

---

## 📝 3. Estándar de Conventional Commits (Obligatorio en Español 🇪🇸)

> [!IMPORTANT]
> **Regla fundamental**: Todos los mensajes de commit, descripciones y cuerpos explicativos deben redactarse **estrictamente en español**.

Cada commit debe seguir la estructura:
```text
<tipo>(<ámbito opcional>): <descripción concisa en imperativo y en español>

[cuerpo explicativo opcional en español]

[pie de commit o referencias opcionales]
```

### Tipos Permitidos y Ejemplos en Español:
- **`feat`**: Una nueva funcionalidad para el usuario/API.
  - *Ejemplo:* `feat(auth): implementar verificación de tokens Google OAuth2 y endpoints jwt`
- **`fix`**: Corrección de un error o bug.
  - *Ejemplo:* `fix(cors): permitir dominio de producción de railway en orígenes autorizados`
- **`docs`**: Cambios exclusivos en documentación o comentarios.
  - *Ejemplo:* `docs(readme): actualizar instrucciones de configuración de la api y variables de entorno`
- **`test`**: Añadir o corregir pruebas unitarias o de integración.
  - *Ejemplo:* `test(auth): agregar pruebas simuladas para verificación de google oauth`
- **`refactor`**: Cambios de código que no corrigen bugs ni añaden funcionalidades.
  - *Ejemplo:* `refactor(serializers): optimizar consulta de serialización del perfil de usuario`
- **`chore`**: Tareas de mantenimiento, dependencias o configuración CI/CD.
  - *Ejemplo:* `chore(deps): actualizar versión de djangorestframework en pyproject.toml`

---

## 🛠️ 4. Paso a Paso: ¿Cómo commitear un nuevo cambio?

Cuando vayas a pedir o desarrollar un nuevo cambio en el proyecto, sigue este flujo riguroso:

### Paso 1: Asegurarse de partir desde `beta` actualizado
```bash
# Cambiar a beta y traer lo último
git checkout beta
git pull origin beta
```

### Paso 2: Crear la rama para tu cambio o funcionalidad
```bash
# Para una nueva función:
git checkout -b feature/nombre-de-tu-funcionalidad

# O para una corrección:
git checkout -b fix/nombre-del-bug
```

### Paso 3: Trabajar los cambios y verificar el estado
```bash
git status
```

### Paso 4: Añadir y commitear con Conventional Commits
```bash
# Agregar archivos específicos
git add codiselu/views.py codiselu/urls.py

# Crear el commit estructurado (en español)
git commit -m "feat(eventos): agregar filtrado por ciudad y fecha en listado de eventos"
```

### Paso 5: Subir la rama a GitHub
```bash
git push -u origin feature/nombre-de-tu-funcionalidad
```

---

## 🔀 5. Proceso de Pull Request y Convergencia (Paso a Paso)

Para garantizar **trazabilidad** y **convergencia**:

### Fase A: Convergencia de Feature a Beta (Pre-lanzamiento)
1. En GitHub, abre un **Pull Request** desde tu rama `feature/nombre-de-tu-funcionalidad` hacia la rama base `beta`.
2. Se cargará automáticamente la plantilla `.github/pull_request_template.md`.
3. Completa el checklist y vincula el issue/requerimiento correspondiente.
4. Una vez revisado y pasadas las pruebas, se realiza el **Merge** hacia `beta`.

*(Equivalente en terminal local si no se usa la interfaz web de GitHub)*:
```bash
git checkout beta
git merge --no-ff feature/nombre-de-tu-funcionalidad -m "Merge pull request #X from feature/nombre-de-tu-funcionalidad into beta"
git tag -a v1.X.X-beta -m "Release Candidate v1.X.X-beta"
```

### Fase B: Convergencia de Beta a Master (Producción)
1. Tras validar la estabilidad en `beta` con usuarios y pruebas finales, se crea un Pull Request de `beta` hacia `master`.
2. Al fusionar en `master`, se etiqueta la versión estable de producción con SemVer:
```bash
git checkout master
git merge --no-ff beta -m "Merge pull request #Y from beta into master - Release v1.X.X"
git tag -a v1.X.X -m "Production Release v1.X.X"
```

---

## 🔍 6. Comandos para Verificar la Trazabilidad y el Grafo

Para comprobar el árbol visual de convergencia en tu terminal:

```bash
# Ver el grafo completo de ramas, tags y convergencia
git log --graph --oneline --decorate --all

# Ver solo las ramas existentes (locales y remotas)
git branch -a

# Ver las etiquetas de versión (tags)
git tag -n
```
