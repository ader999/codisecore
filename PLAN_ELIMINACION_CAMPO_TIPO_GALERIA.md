# Plan de Deprecación y Eliminación del Campo `tipo` en GaleriaMultimedia

> **Fecha Programada de Ejecución:** A partir del **16 de Septiembre de 2026**  
> **Estado:** 🟡 Programado / En Espera de Transición de Clientes Móviles  
> **Módulo:** `codiselu`  
> **Objetivo:** Retirar el campo redundante `tipo` (`Imagen` / `Video`) del modelo `GaleriaMultimedia` para simplificar la administración, eliminando la necesidad de selección manual.

---

## 1. Justificación y Análisis de Impacto

### ¿Por qué se programa para después del 15 de septiembre de 2026?
1. **Compatibilidad hacia atrás con la App Móvil (`CodiceLuAppMovil`):**  
   Las versiones anteriores de la aplicación móvil (instaladas vía APK previa) consumen el campo `"tipo"` para decidir si instancian reproductores multimedia o visores de fotos (`if (item['tipo'] == 'Video')`).
2. **Ventana de actualización de usuarios:**  
   Esta ventana de tiempo permite que los usuarios descarguen e instalen la versión actualizada de la aplicación móvil, la cual inferirá el tipo de recurso directamente según la presencia de los campos (`video_archivo` / `video_url` vs `imagen`).
3. **Cero tiempo de inactividad o fallos en producción:**  
   Evita excepciones de tipo `MissingKeyException` o `NullPointerException` en clientes desactualizados.

---

## 2. Fase de Preparación Previa (Antes del 15 de Septiembre)

### En la App Móvil (`CodiceLuAppMovil`):
Actualizar los modelos de datos en Flutter/Dart para que no dependan exclusivamente del campo `tipo`:
```dart
// En el modelo de GaleriaMultimedia:
factory GaleriaMultimedia.fromJson(Map<String, dynamic> json) {
  final tieneVideo = (json['video_archivo'] != null && json['video_archivo'].toString().isNotEmpty) ||
                     (json['video_url'] != null && json['video_url'].toString().isNotEmpty);
                     
  final tipoCalculado = json['tipo'] ?? (tieneVideo ? 'Video' : 'Imagen');

  return GaleriaMultimedia(
    id: json['id'],
    titulo: json['titulo'],
    tipo: tipoCalculado,
    imagen: json['imagen'],
    videoArchivo: json['video_archivo'],
    videoUrl: json['video_url'],
  );
}
```

---

## 3. Guía de Ejecución Técnica (Después del 15 de Septiembre de 2026)

Llegada la fecha programada, sigue estos pasos secuenciales:

### Paso 1: Actualizar el Modelo (`codiselu/models.py`)
Ubicar la clase `GaleriaMultimedia` y remover la definición del campo `tipo` y `TIPO_CHOICES`:

```python
# 1. Eliminar TIPO_CHOICES:
# TIPO_CHOICES = [
#     ('Imagen', 'Imagen'),
#     ('Video', 'Video'),
# ]

# 2. Eliminar la columna tipo:
# tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='Imagen')
```

Actualizar el método `__str__`:
```python
def __str__(self):
    origen = self.ciudad.nombre if self.ciudad else (self.punto_interes.nombre if self.punto_interes else (self.evento.titulo if self.evento else "General"))
    tipo_str = "Video" if (self.video_archivo or self.video_url) else "Imagen"
    return f"{tipo_str}: {self.titulo or 'Sin título'} [{origen}]"
```

---

### Paso 2: Adaptar el Serializador (`codiselu/serializers.py`)
Para garantizar que cualquier cliente aún rezagado no falle, podemos mantener `"tipo"` en el JSON de salida como un `SerializerMethodField` dinámico sin ocupar espacio en base de datos:

```python
class GaleriaMultimediaSerializer(serializers.ModelSerializer):
    tipo = serializers.SerializerMethodField()

    class Meta:
        model = GaleriaMultimedia
        fields = ['id', 'ciudad', 'punto_interes', 'evento', 'titulo', 'tipo', 'imagen', 'video_archivo', 'video_url']

    def get_tipo(self, obj):
        if obj.video_archivo or obj.video_url:
            return "Video"
        return "Imagen"
```
*(Si ya no se requiere enviar `"tipo"` en el payload, simplemente retirar `'tipo'` de `fields`).*

---

### Paso 3: Limpiar el Panel de Control Codice路 (`codiselu/admin.py`)
Actualizar `GaleriaMultimediaInline` y `GaleriaMultimediaAdmin`:

```python
class GaleriaMultimediaInline(admin.TabularInline):
    model = GaleriaMultimedia
    extra = 1
    fields = ('titulo', 'imagen', 'video_archivo', 'video_url')  # Se retira 'tipo'

@admin.register(GaleriaMultimedia)
class GaleriaMultimediaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'ciudad', 'punto_interes', 'evento', 'recurso_multimedia')
    list_filter = ('ciudad', 'evento')  # Se retira 'tipo'
    search_fields = ('titulo', 'ciudad__nombre', 'punto_interes__nombre', 'evento__titulo')
    fields = ('ciudad', 'punto_interes', 'evento', 'titulo', 'imagen', 'video_archivo', 'video_url')
```

---

### Paso 4: Actualizar Pruebas Unitarias (`codiselu/tests.py`)
Eliminar el argumento `tipo="..."` en las llamadas a `GaleriaMultimedia.objects.create(...)`:
```python
GaleriaMultimedia.objects.create(
    ciudad=ciudad,
    titulo="Foto Panorámica León"
    # Se retira tipo="Imagen"
)
```

---

### Paso 5: Generar y Aplicar Migración en Base de Datos

```bash
# 1. Generar la migración de eliminación
.venv/bin/python manage.py makemigrations codiselu --name remove_galeriamultimedia_tipo

# 2. Verificar el SQL generado
.venv/bin/python manage.py sqlmigrate codiselu <numero_migracion>

# 3. Aplicar a la base de datos
.venv/bin/python manage.py migrate
```

---

### Paso 6: Verificación y Pruebas

```bash
# Comprobación del sistema
.venv/bin/python manage.py check

# Ejecución de la suite de pruebas
.venv/bin/python manage.py test codiselu.tests.CiudadesYContenidoApiTests --keepdb
```

---

## 4. Plan de Rollback (Contingencia)

En caso de requerir revertir la migración:
1. Revertir la migración en la base de datos:
   ```bash
   .venv/bin/python manage.py migrate codiselu 0010_galeriamultimedia_video_archivo_and_more
   ```
2. Revertir los cambios en Git:
   ```bash
   git restore codiselu/models.py codiselu/admin.py codiselu/serializers.py codiselu/tests.py
   ```
