import math
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    User, Ciudad, CircuitoCreativo, PuntoInteres, DatoHistorico,
    GaleriaMultimedia, UsuarioPuntoVisitado, Empresa, OportunidadInversion,
    InversionTurista, Evento, EventoAsistencia, Publicacion, PublicacionImagen
)


def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en metros entre dos puntos geográficos usando la fórmula de Haversine.
    """
    R = 6371000  # Radio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(R * c, 2)



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'es_protagonista', 'es_turista', 'telefono', 'foto_perfil',
            'is_staff', 'is_active'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'es_protagonista', 'es_turista',
            'telefono', 'foto_perfil'
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un usuario registrado con este correo electrónico.")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)

        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})

        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, help_text="Nombre de usuario o correo electrónico")
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        username_or_email = attrs.get('username')
        password = attrs.get('password')

        user = None
        if '@' in username_or_email:
            try:
                found_user = User.objects.get(email__iexact=username_or_email)
                user = authenticate(username=found_user.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(username=username_or_email, password=password)

        if not user:
            raise serializers.ValidationError("Credenciales inválidas. Por favor verifica tu usuario/correo y contraseña.")

        if not user.is_active:
            raise serializers.ValidationError("Esta cuenta de usuario está desactivada.")

        attrs['user'] = user
        return attrs


class DatoHistoricoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatoHistorico
        fields = ['id', 'ciudad', 'punto_interes', 'titulo', 'tipo', 'contenido', 'epoca_o_ano']


class GaleriaMultimediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GaleriaMultimedia
        fields = ['id', 'ciudad', 'punto_interes', 'evento', 'titulo', 'tipo', 'imagen', 'video_url']


class PuntoInteresSerializer(serializers.ModelSerializer):
    datos_historicos = DatoHistoricoSerializer(many=True, read_only=True)
    galeria = GaleriaMultimediaSerializer(many=True, read_only=True)
    circuito_nombre = serializers.ReadOnlyField(source='circuito.nombre')

    class Meta:
        model = PuntoInteres
        fields = [
            'id', 'circuito', 'circuito_nombre', 'nombre', 'descripcion',
            'tipo', 'orden', 'latitud', 'longitud', 'datos_historicos', 'galeria'
        ]


class CircuitoCreativoSerializer(serializers.ModelSerializer):
    ciudad_nombre = serializers.ReadOnlyField(source='ciudad.nombre')
    puntos_interes = PuntoInteresSerializer(many=True, read_only=True)

    class Meta:
        model = CircuitoCreativo
        fields = [
            'id', 'ciudad', 'ciudad_nombre', 'nombre', 'descripcion',
            'distancia_km', 'duracion_estimada', 'dificultad', 'imagen_mapa',
            'puntos_interes'
        ]


class CiudadSerializer(serializers.ModelSerializer):
    circuitos = CircuitoCreativoSerializer(many=True, read_only=True)
    datos_historicos = DatoHistoricoSerializer(many=True, read_only=True)
    galeria = GaleriaMultimediaSerializer(many=True, read_only=True)

    class Meta:
        model = Ciudad
        fields = [
            'id', 'nombre', 'descripcion', 'imagen_portada',
            'latitud_centro', 'longitud_centro', 'circuitos',
            'datos_historicos', 'galeria'
        ]


class UsuarioPuntoVisitadoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.ReadOnlyField(source='usuario.id')
    punto_interes_id = serializers.PrimaryKeyRelatedField(
        queryset=PuntoInteres.objects.all(),
        source='punto_interes',
        required=False
    )
    punto_interes = serializers.PrimaryKeyRelatedField(
        queryset=PuntoInteres.objects.all(),
        required=False
    )
    punto_interes_nombre = serializers.ReadOnlyField(source='punto_interes.nombre')
    circuito_nombre = serializers.ReadOnlyField(source='punto_interes.circuito.nombre')
    ciudad_nombre = serializers.ReadOnlyField(source='punto_interes.circuito.ciudad.nombre')

    class Meta:
        model = UsuarioPuntoVisitado
        fields = [
            'id', 'usuario', 'usuario_id', 'punto_interes', 'punto_interes_id',
            'punto_interes_nombre', 'circuito_nombre', 'ciudad_nombre', 'fecha_visita',
            'latitud_usuario', 'longitud_usuario', 'es_validada', 'distancia_metros'
        ]
        read_only_fields = ['id', 'usuario', 'usuario_id', 'es_validada', 'distancia_metros']

    def validate(self, attrs):
        if 'punto_interes' not in attrs:
            raise serializers.ValidationError({"punto_interes_id": "Este campo es requerido (debe enviar punto_interes_id o punto_interes)."})
        return attrs

    def _calcular_validacion(self, punto_interes, lat_user, lon_user):
        if lat_user is not None and lon_user is not None:
            distancia = calcular_distancia_haversine(
                float(lat_user), float(lon_user),
                float(punto_interes.latitud), float(punto_interes.longitud)
            )
            # Umbral de validación por proximidad: 200 metros
            es_validada = distancia <= 200.0
            return distancia, es_validada
        return None, False

    def create(self, validated_data):
        usuario = self.context['request'].user
        punto_interes = validated_data['punto_interes']
        fecha_visita = validated_data.get('fecha_visita')
        lat_user = validated_data.get('latitud_usuario')
        lon_user = validated_data.get('longitud_usuario')

        distancia, es_validada = self._calcular_validacion(punto_interes, lat_user, lon_user)

        defaults = {
            'latitud_usuario': lat_user,
            'longitud_usuario': lon_user,
            'distancia_metros': distancia,
            'es_validada': es_validada
        }
        if fecha_visita:
            defaults['fecha_visita'] = fecha_visita

        visita, created = UsuarioPuntoVisitado.objects.get_or_create(
            usuario=usuario,
            punto_interes=punto_interes,
            defaults=defaults
        )
        if not created:
            visita.latitud_usuario = lat_user
            visita.longitud_usuario = lon_user
            visita.distancia_metros = distancia
            visita.es_validada = es_validada
            if fecha_visita:
                visita.fecha_visita = fecha_visita
            visita.save()

        return visita


class EmpresaSerializer(serializers.ModelSerializer):
    usuario_username = serializers.ReadOnlyField(source='usuario.username')
    ciudad_nombre = serializers.ReadOnlyField(source='ciudad.nombre')
    punto_interes_nombre = serializers.ReadOnlyField(source='punto_interes.nombre')

    class Meta:
        model = Empresa
        fields = [
            'id', 'usuario', 'usuario_username', 'ciudad', 'ciudad_nombre',
            'punto_interes', 'punto_interes_nombre', 'nombre', 'descripcion',
            'categoria', 'direccion', 'telefono_contacto', 'email_contacto',
            'sitio_web', 'imagen_portada', 'latitud', 'longitud',
            'acepta_inversiones', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'usuario', 'usuario_username', 'fecha_creacion']


class OportunidadInversionSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    empresa_acepta_inversiones = serializers.ReadOnlyField(source='empresa.acepta_inversiones')

    class Meta:
        model = OportunidadInversion
        fields = [
            'id', 'empresa', 'empresa_nombre', 'empresa_acepta_inversiones',
            'titulo', 'descripcion', 'monto_requerido', 'monto_minimo_inversion',
            'monto_recaudado', 'retorno_estimado', 'tipo_inversor_permitido',
            'esta_activa', 'fecha_publicacion'
        ]
        read_only_fields = ['id', 'fecha_publicacion']

    def validate(self, attrs):
        empresa = attrs.get('empresa')
        if empresa and not empresa.acepta_inversiones:
            raise serializers.ValidationError({
                "empresa": "Esta empresa o destino turístico no tiene habilitada la opción de aceptar inversiones."
            })
        return attrs


class InversionTuristaSerializer(serializers.ModelSerializer):
    inversionista_username = serializers.ReadOnlyField(source='inversionista.username')
    empresa_id = serializers.ReadOnlyField(source='oportunidad.empresa.id')
    empresa_nombre = serializers.ReadOnlyField(source='oportunidad.empresa.nombre')
    oportunidad_titulo = serializers.ReadOnlyField(source='oportunidad.titulo')

    class Meta:
        model = InversionTurista
        fields = [
            'id', 'inversionista', 'inversionista_username', 'oportunidad',
            'oportunidad_titulo', 'empresa_id', 'empresa_nombre',
            'monto_propuesto', 'tipo_inversor', 'mensaje', 'telefono_inversor',
            'email_inversor', 'estado', 'fecha_solicitud'
        ]
        read_only_fields = ['id', 'inversionista', 'inversionista_username', 'estado', 'fecha_solicitud']

    def validate(self, attrs):
        oportunidad = attrs.get('oportunidad')
        if oportunidad:
            if not oportunidad.empresa.acepta_inversiones:
                raise serializers.ValidationError({
                    "oportunidad": "La empresa asociada a esta oportunidad de inversión no acepta inversiones actualmente."
                })
            if not oportunidad.esta_activa:
                raise serializers.ValidationError({
                    "oportunidad": "Esta oportunidad de inversión no se encuentra activa."
                })
            monto = attrs.get('monto_propuesto')
            if monto and monto < oportunidad.monto_minimo_inversion:
                raise serializers.ValidationError({
                    "monto_propuesto": f"El monto propuesto no puede ser menor al monto mínimo de inversión (${oportunidad.monto_minimo_inversion})."
                })
        return attrs


class PublicacionImagenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicacionImagen
        fields = ['id', 'imagen', 'fecha_creacion']


class PublicacionSerializer(serializers.ModelSerializer):
    autor_username = serializers.ReadOnlyField(source='autor.username')
    autor_foto_perfil = serializers.ImageField(source='autor.foto_perfil', read_only=True)
    es_protagonista = serializers.ReadOnlyField(source='autor.es_protagonista')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    ciudad_nombre = serializers.ReadOnlyField(source='ciudad.nombre')
    evento_titulo = serializers.ReadOnlyField(source='evento.titulo')
    imagenes = PublicacionImagenSerializer(many=True, read_only=True)
    total_likes = serializers.ReadOnlyField()
    user_ha_dado_like = serializers.SerializerMethodField()

    class Meta:
        model = Publicacion
        fields = [
            'id', 'autor', 'autor_username', 'autor_foto_perfil', 'es_protagonista',
            'empresa', 'empresa_nombre', 'ciudad', 'ciudad_nombre',
            'evento', 'evento_titulo', 'titulo', 'descripcion',
            'imagen_principal', 'video_url', 'imagenes', 'total_likes',
            'user_ha_dado_like', 'esta_activa', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'autor', 'autor_username', 'autor_foto_perfil', 'es_protagonista', 'total_likes', 'user_ha_dado_like', 'fecha_creacion']

    def get_user_ha_dado_like(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False


class EventoSerializer(serializers.ModelSerializer):
    creador_username = serializers.ReadOnlyField(source='creador.username')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    ciudad_nombre = serializers.ReadOnlyField(source='ciudad.nombre')
    en_mural = serializers.ReadOnlyField()
    total_granos_cafe = serializers.ReadOnlyField()
    user_ha_dado_grano_cafe = serializers.SerializerMethodField()
    total_asistentes = serializers.ReadOnlyField()
    user_va_a_asistir = serializers.SerializerMethodField()
    galeria = GaleriaMultimediaSerializer(many=True, read_only=True)
    publicaciones = PublicacionSerializer(many=True, read_only=True)

    class Meta:
        model = Evento
        fields = [
            'id', 'creador', 'creador_username', 'empresa', 'empresa_nombre',
            'ciudad', 'ciudad_nombre', 'titulo', 'descripcion', 'fecha_inicio',
            'fecha_fin', 'ubicacion', 'latitud', 'longitud', 'imagen',
            'precio_entrada', 'es_gratuito', 'cupo_maximo', 'es_oficial',
            'dias_previos_mural', 'en_mural', 'esta_activo', 'total_granos_cafe',
            'user_ha_dado_grano_cafe', 'total_asistentes', 'user_va_a_asistir',
            'galeria', 'publicaciones', 'fecha_creacion'
        ]
        read_only_fields = [
            'id', 'creador', 'creador_username', 'en_mural', 'total_granos_cafe',
            'user_ha_dado_grano_cafe', 'total_asistentes', 'user_va_a_asistir', 'fecha_creacion'
        ]

    def get_user_ha_dado_grano_cafe(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.granos_cafe.filter(id=request.user.id).exists()
        return False

    def get_user_va_a_asistir(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.asistencias.filter(usuario=request.user).exists()
        return False

